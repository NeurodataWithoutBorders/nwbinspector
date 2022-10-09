from setuptools import setup, find_packages
from pathlib import Path
from shutil import copy

root = Path(__file__).parent
with open(root / "README.md", "r") as f:
    long_description = f.read()
with open(root / "requirements.txt") as f:
    install_requires = f.readlines()
with open(root / "src" / "nwbinspector" / "version.py") as f:
    version = f.read()

# Instantiate the testing configuration file from the base file `base_test_config.json`
base_test_config = Path.cwd() / "base_test_config.json"
local_test_config = Path.cwd() / "tests" / "testing_config.json"
if not local_test_config.exists():
    copy(src=base_test_config, dst=local_test_config)

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
    extras_require=dict(dandi=["dandi>=0.39.2"]),
    entry_points={"console_scripts": ["nwbinspector=nwbinspector.nwbinspector:inspect_all_cli"]},
    license="BSD-3-Clause",
)
