from setuptools import setup, find_packages

# Get the long description from the README file
with open("README.md", "r") as f:
    long_description = f.read()
setup(
    name="nwbinspector",
    version="0.3.1",
    description="Tool to inspect NWB files for best practices compliance.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Ryan Ly, Ben Dichter, and Cody Baker.",
    author_email="rly@lbl.gov, ben.dichter@gmail.com, cody.baker@catalystneuro.com",
    packages=find_packages(),
    include_package_data=True,
    url="https://github.com/NeurodataWithoutBorders/nwbinspector",
    install_requires=["pynwb", "natsort", "click", "PyYAML", "jsonschema"],
    entry_points={"console_scripts": ["nwbinspector=nwbinspector.nwbinspector:inspect_all_cli"]},
)
