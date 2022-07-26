from setuptools import setup, find_packages
from pathlib import Path

root = Path(__file__).parent
with open(root / "README.md", "r") as f:
    long_description = f.read()
with open(root / "requirements.txt") as f:
    install_requires = f.readlines()
setup(
    name="nwbinspector",
    version="0.4.12",
    description="Tool to inspect NWB files for best practices compliance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ryan Ly, Ben Dichter, and Cody Baker.",
    author_email="rly@lbl.gov, ben.dichter@gmail.com, cody.baker@catalystneuro.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/NeurodataWithoutBorders/nwbinspector",
    install_requires=install_requires,
    extras_require=dict(dandi=["dandi>=0.39.2"]),
    entry_points={"console_scripts": ["nwbinspector=nwbinspector.nwbinspector:inspect_all_cli"]},
    license="BSD-3-Clause",
)
