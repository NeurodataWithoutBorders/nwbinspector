A set of internal tools to help inspect NWB files for compliance with [NWB Best Practices](https://www.nwb.org/best-practices/). This inspector is meant as a companion to the pynwb validator, which checks for strict schema compliance. In contrast, this tool attempts to apply some common sense to find components of the file that are technically compliant, but probably incorrect, or suboptimal, or deviate from best practices. This tool is meant simply as a data review aid. It does not catch all best practice violations, and any warnings it does produce should be checked by a knowledgeable reviewer.

This project is under active development. You may use this as a stand-alone tool, but we do not advise you to code against this project at this time as we do expect the warnings to change as the project develops.

## Installation
```bash
pip install nwbinspector
```

## Usage

```bash
# supply a path to an NWB file
nwbinspector path/to/my/data.nwb  

# supply a path to a directory containing NWB files
nwbinspector path/to/my/data/dir/

# optional: supply modules to import before reading the file, e.g., for NWB extensions
nwbinspector path/to/my/data.nwb -m my_extension_module1 my_extension_module2
```
