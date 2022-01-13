from setuptools import setup

setup(
    name="cafaz",
    version="0.2.0",
    description="To read CAFE60 on AWS from NCI",
    url="https://github.com/coecms/CAFEAWS",
    author="Claire Carouge",
    author_email="c.carouge@unsw.edu.au",
    license="Apache 2.0",
    packages=["cafaz"],
    install_requires=[
        "xarray",
        "dask",
        "s3fs",
        "fsspec",
        "kerchunk",
        "ujson",
    ],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: BSD License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.9",
    ],
)
