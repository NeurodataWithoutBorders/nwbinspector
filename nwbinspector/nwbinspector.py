"""Cody Baker, Ben Dichter, and Ryan Ly."""
import argparse
import importlib
import pathlib
from collections import defaultdict
from typing import Optional

import pynwb

from . import available_checks


def main():
    """
    Primary command line function for checking an NWBFile for format improvements.

    Usage: python nwbinspector.py dir_name
    """
    parser = argparse.ArgumentParser("python test.py [options]")
    parser.add_argument(
        "-m",
        "--modules",
        nargs="*",
        dest="modules",
        help="modules to import prior to reading the file(s)",
    )
    parser.add_argument("path", help="path to an NWB file or directory containing NWB files")
    parser.set_defaults(modules=[])
    args = parser.parse_args()

    in_path = pathlib.Path(args.path)
    if in_path.is_dir():
        files = list(in_path.glob("*.nwb"))
    elif in_path.is_file():
        files = [in_path]
    else:
        raise ValueError("%s should be a directory or an NWB file" % in_path)

    for module in args.modules:
        importlib.import_module(module)

    num_invalid_files = 0
    num_exceptions = 0
    for fi, filename in enumerate(files):
        print("%d/%d %s" % (fi + 1, len(files), filename))

        try:
            with pynwb.NWBHDF5IO(str(filename), "r", load_namespaces=True) as io:
                errors = pynwb.validate(io)
                if errors:
                    for e in errors:
                        print("Validator Error:", e)
                    num_invalid_files += 1
                else:
                    print("Validation OK!")

                nwbfile = io.read()
                # TODO, pass optional arguments from cmd line to inspect_nwb
                check_results = inspect_nwb(nwbfile=nwbfile)
                print(check_results)
        except Exception as ex:
            num_exceptions += 1
            print("ERROR:", ex)

    if num_invalid_files:
        print("%d/%d files are invalid." % (num_exceptions, num_invalid_files))
    if num_exceptions:
        print("%d/%d files had errors." % (num_exceptions, num_exceptions))


def inspect_nwb(
    nwbfile: pynwb.NWBFile,
    checks=available_checks,
    severity_threshold: int = 0,
    skip: Optional[list] = None,
):
    """
    Inspect a NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile : pynwb.NWBFile
        The open NWBFile object to test.
    checks : dictionary, optional
        A nested dictionary specifying which quality checks to run.
        Outer key is severity (between 1 to 3 inclusive, 3 being most severe).
        Each severity is mapped to a dictionary whose keys are NWBFile object types.
        The value of each object type is a list of test functions to run.

        # TODO change the below import
        This can be modified or extended by calling `from nwbinspector.refactor_inspector import available_checks`,
        then updating or appending `available_checks` as desired, then passing into this function call.
        By default, all availaable checks are run.
    severity_threshold : integer, optional
        Ignores tests with an assigned severity below this threshold.
        Severity has three levels:
            3: most severe
                - probably incorrect data
            2: medium severity
                - possibly incorrect data
                - very suboptimal data representation
            1: low severity
                - improvable data representation
        The default is 0.
    skip: list, optional
        Names of functions to skip.
    """
    check_results = defaultdict(list)
    for severity, severity_checks in checks.items():
        if severity < severity_threshold:
            continue
        for check_object_type, check_functions in severity_checks.items():
            for obj in nwbfile.objects.values():
                if issubclass(type(obj), check_object_type):
                    for check_function in check_functions:
                        if skip is not None and check_function.__name__ in skip:
                            continue
                        output = check_function(obj)
                        if output is None:
                            continue
                        check_results[severity].append(
                            dict(
                                check_function_name=check_function.__name__,
                                object_type=type(obj).__name__,
                                object_name=obj.name,
                                output=output,
                            )
                        )
    return check_results


if __name__ == "__main__":
    main()
