Using the Command Line Interface (CLI)
======================================

The NWBInspector tool offers convenient command-line usage via any standard Conda or IPython terminal.

You may then run the NWBInspector via the command line via the following usages

```bash
# supply a path to a single NWBFile
nwbinspector path/to/my/data.nwb

# supply a path to a directory containing several NWBFiles (this will recurse to subdirectories)
nwbinspector path/to/my/data/dir/
```

which should quickly display a basic report to your console window.

(# TODO, maybe show an example of basic output here)

There are many common options you can specify with flags, such as

```bash
# save report for subsequent reference
nwbinspector path/to/my/data.nwb --log-file path/to/my/nwbinspector_report.txt

# if a report file from a previous run of the inspector is already present
# at the location, it can be optionally overwritten with '-o'
nwbinspector path/to/my/data.nwb -o --log-file path/to/my/nwbinspector_report.txt

# supply external modules to import before reading the file, e.g., for NWB extensions
nwbinspector path/to/my/data.nwb -m my_extension_module1 my_extension_module2

# specify the number of jobs to run in parallel (only works in directory mode)
# '--n-jobs -1' will automatically use as many resources as are available on your system
nwbinspector path/to/my/data/dir/ --n-jobs -1
```

Other flags may be viewed in the command line by calling `nwbinspector --help`.
