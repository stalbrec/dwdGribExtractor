from setuptools import setup, find_packages
import dwdGribExtractor

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='dwdGribExtractor',
    version=dwdGribExtractor.__version__,
    author='Manuel Strohmaier',
    author_email='manuel.strohmaier@joanneum.at',
    description="API for DWD's open weather grib data.",
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url="https://github.com/prayer007/dwdGribExtractor",
    project_urls={
        'Documentation': 'https://github.com/prayer007/dwdGribExtractor',
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    install_requires=[
        'requests',
        'multiprocess',
        'xarray',
        'pandas',
        'cfgrib',
        'eccodes',
        'netCDF4'
    ]
)
