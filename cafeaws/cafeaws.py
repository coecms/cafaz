import s3fs
import xarray as xr
import kerchunk.hdf
import dask
import ujson
import fsspec
import os
from pathlib import Path


class cafeaws(object):
    def __init__(
        self, varname, realm, time_res, json_root="/g/data/w35/ccc561/CAFE60/json"
    ):
        """
        realm: str, one of the realms for the CAFE variables
        varname: str, name of one of the CAFE variables
        time_res: 'daily'|'month', temporal resolution for the variable
        json_root: str or Path, path where to store the JSON files"""

        self.root = Path("cafe60-reanalysis-dataset-aws-open-data")
        self.varname = varname
        self.realm = realm
        self.time_res = time_res
        self.json_root = Path(json_root)

    def find_cafe_files(self):
        """Return a list of all the files for the given variable defined in self"""

        fs = s3fs.S3FileSystem(anon=True)
        path = self.root / self.realm

        my_list = fs.glob(f"{path}/{self.varname}.{self.realm}.{self.time_res}.*")

        # Stop and return an error message if no files found.
        assert (
            len(my_list) != 0
        ), "There is no such variable in that realm or for that temporal resolution. Please check the CAFE documentation."
        return my_list

    @staticmethod
    def gen_json(u, json_dir):
        fs = s3fs.S3FileSystem(anon=True)
        so = dict(
            mode="rb", anon=True, default_fill_cache=False, default_cache_type="first"
        )

        with fs.open(u, **so) as infile:
            h5chunks = kerchunk.hdf.SingleHdf5ToZarr(infile, u, inline_threshold=300)
            p = u.split("/")
            fname = p[4]
            outf = f"{json_dir}/{fname}.json"
            with open(outf, "wb") as f:
                f.write(ujson.dumps(h5chunks.translate()).encode())

    def write_json(self):
        """Generate the JSON files for all the netcdf files for that variable"""

        file_list = self.find_cafe_files()
        urls = ["s3://" + f for f in file_list]
        json_path = self.json_root / self.realm
        os.makedirs(json_path, exist_ok=True)
        dask.compute(
            *[dask.delayed(self.gen_json)(u, json_path) for u in urls], retries=10
        )

    def read_CAFE(self):
        """Read the full timeseries for the variable defined"""

        json_path = self.json_root / self.realm
        json_list = sorted(
            json_path.glob(f"{self.varname}.{self.realm}.{self.time_res}*.json")
        )
        m_list = []
        for js in json_list:
            with open(js) as f:
                m_list.append(
                    fsspec.get_mapper(
                        "reference://",
                        fo=ujson.load(f),
                        remote_protocol="s3",
                        remote_options={"anon": True},
                    )
                )
        ds1 = xr.open_mfdataset(
            m_list,
            combine="nested",
            concat_dim="time",
            engine="zarr",
            coords="minimal",
            data_vars="minimal",
            compat="override",
            parallel=True,
        )
        return ds1
