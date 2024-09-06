from pathlib import Path

from setuptools import find_packages, setup

root = Path(__file__).parent
with open(root / "README.md", "r") as f:
    long_description = f.read()
with open(root / "requirements.txt") as f:
    install_requires = f.readlines()
with open(root / "src" / "nwbinspector" / "_version.py") as f:
    version = f.read()

setup(
    name="nwbinspector",
    version=version.split('"')[1],
    description="Tool to inspect NWB files for best practices compliance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ryan Ly, Ben Dichter, and Cody Baker.",
    author_email="rly@lbl.gov, ben.dichter@gmail.com, cody.baker@catalystneuro.com",
    url="https://nwbinspector.readthedocs.io/",
    keywords="nwb",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,  # Includes files described in MANIFEST.in in the installation
    install_requires=install_requires,
    # zarr<2.18.0 because of https://github.com/NeurodataWithoutBorders/nwbinspector/pull/460
    extras_require=dict(dandi=["dandi>=0.39.2", "zarr<2.18.0", "remfile"], zarr=["hdmf_zarr>=0.3.0", "zarr<2.18.0"]),
    entry_points={"console_scripts": ["nwbinspector=nwbinspector._nwbinspector_cli:_nwbinspector_cli"]},
    license="BSD-3-Clause",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
