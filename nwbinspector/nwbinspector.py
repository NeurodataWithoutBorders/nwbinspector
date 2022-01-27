"""Cody Baker, Ben Dichter, and Ryan Ly."""
import argparse
import importlib
import pathlib
from typing import Optional

import pynwb

from . import available_checks, importance_levels


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


def sort_check_results(check_results: list):
    """Sort the list of returned results from checks according to importance levels followed by severity."""
    # TODO
    sorted_check_results = check_results
    return sorted_check_results


def inspect_nwb(
    nwbfile: pynwb.NWBFile,
    checks: list = available_checks,
    importance_threshold: str = "Best Practice Suggestion",
    skip: Optional[list] = None,
):
    """
    Inspect a NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile : pynwb.NWBFile
        The NWBFile object to check.
    checks : dictionary, optional
        A nested dictionary specifying which quality checks to run.
        Outer key is importance, inner key is NWB object type, and values are lists of test functions to run.
        This can be modified or extended by calling `from nwbinspector import available_checks`,
        then modifying `available_checks` as desired prior to passing into this function.
        By default, all available checks are run.
    importance_threshold : string, optional
        Ignores tests with an assigned importance below this threshold.
        Importance has four levels:
            Critical
                - potentially incorrect data
            DANDI Requirement
                - possibly incorrect data
                - very suboptimal data representation
            Best Practice Violation
                - very suboptimal data representation
            Best Practice Suggestion
                - improvable data representation
        The default is the lowest level, 'Best Practice Suggestions'.
    skip: list, optional
        Names of functions to skip.
    """
    check_results = list()
    ordinal_importance_levels = {importance_level: j for j, importance_level in enumerate(importance_levels)}
    for importance, checks_per_object_type in checks.items():
        if ordinal_importance_levels[importance] >= ordinal_importance_levels[importance_threshold]:
            for check_object_type, check_functions in checks_per_object_type.items():
                for obj in nwbfile.objects.values():
                    if issubclass(type(obj), check_object_type):
                        for check_function in check_functions:
                            if skip is not None and check_function.__name__ in skip:
                                continue
                            output = check_function(obj)
                            if output is None:
                                continue
                            check_results.append(output)
    sorted_check_results = sort_check_results(check_results)
    return sorted_check_results


if __name__ == "__main__":
    main()
