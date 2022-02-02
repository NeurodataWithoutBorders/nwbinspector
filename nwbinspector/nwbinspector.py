"""Cody Baker, Ben Dichter, and Ryan Ly."""
import os
import argparse
import importlib
import traceback
from typing import Optional
from pathlib import Path

import pynwb
from natsort import natsorted

from . import available_checks, Importance
from .inspector_tools import organize_inspect_results, write_results, print_to_console


def main():
    """
    Primary command line function for checking an NWBFile for format improvements.

    Usage: python nwbinspector.py nwbfile_name.nwb
           python nwbinspector.py directory_path
    """
    parser = argparse.ArgumentParser("python test.py [options]")
    parser.add_argument(
        "-m",
        "--modules",
        nargs="*",
        dest="modules",
        help="Modules to import prior to reading the file(s).",
    )
    parser.add_argument("path", help="Path to an NWB file or directory containing NWBFiles.")
    parser.add_argument(
        "-w", "--overwrite", dest="overwrite", default=True, help="Overwrite an existing log file at the location."
    )
    parser.add_argument(
        "-n",
        "--logname",
        dest="log_file_name",
        default="nwbinspector_log_file",
        help="Name of the log file to be saved.",
    )
    parser.add_argument("-s", "--skip", dest="skip", default=None, help="Names of functions to skip.")
    parser.add_argument(
        "-t",
        "--threshold",
        dest="importance_threshold",
        default="BEST_PRACTICE_SUGGESTION",
        help=(
            " Ignores tests with an assigned importance below this threshold. Importance has three levels: "
            "CRITICAL, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION."
        ),
    )
    parser.set_defaults(modules=[])
    args = parser.parse_args()

    in_path = Path(args.path)
    if in_path.is_dir():
        nwbfiles = list(in_path.glob("*.nwb"))
    elif in_path.is_file():
        nwbfiles = [in_path]
    else:
        raise ValueError(f"{in_path} should be a directory or an NWB file.")
    nwbfiles = natsorted(nwbfiles)
    num_nwbfiles = len(nwbfiles)

    for module in args.modules:
        importlib.import_module(module)

    num_invalid_files = 0
    num_exceptions = 0
    organized_results = dict()
    # TODO: perhaps with click, if log file exists, ask user for confirmation to flip overwrite flag
    log_file_path = nwbfiles[0].parent / (args.log_file_name + ".txt")
    for file_index, nwbfile_path in enumerate(nwbfiles):
        print(f"{file_index}/{num_nwbfiles}: {nwbfile_path}")

        try:
            with pynwb.NWBHDF5IO(path=str(nwbfile_path), mode="r", load_namespaces=True) as io:
                errors = pynwb.validate(io)
                if errors:
                    for e in errors:
                        print("Validator Error: ", e)
                    num_invalid_files += 1

                nwbfile = io.read()
                check_results = inspect_nwb(
                    nwbfile=nwbfile, skip=args.skip, importance_threshold=Importance[args.importance_threshold]
                )
                if any(check_results):
                    organized_results.update({str(nwbfile_path): organize_inspect_results(check_results=check_results)})
        except Exception as ex:
            num_exceptions += 1
            print("ERROR: ", ex)
            traceback.print_exc()

    if len(organized_results):
        write_results(log_file_path=log_file_path, organized_results=organized_results, overwrite=args.overwrite)
        print_to_console(log_file_path=log_file_path)
        print(f"{os.linesep*2}Log file saved at {str(log_file_path)}!")
    if num_invalid_files:
        print(f"{num_exceptions}/{num_nwbfiles} files are invalid.")
    if num_exceptions:
        print(f"{num_exceptions}/{num_nwbfiles} files had errors.")


def inspect_nwb(
    nwbfile: pynwb.NWBFile,
    checks: list = available_checks,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
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
        Importance has three levels:
            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation
        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    skip: list, optional
        Names of functions to skip.
    """
    if importance_threshold not in Importance:
        raise ValueError(
            f"Indicated importance_threshold ({importance_threshold}) is not a valid importance level! Please choose "
            "from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION]."
        )

    check_results = list()
    for importance, checks_per_object_type in checks.items():
        if importance.value >= importance_threshold.value:
            for check_object_type, check_functions in checks_per_object_type.items():
                for nwbfile_object in nwbfile.objects.values():
                    if issubclass(type(nwbfile_object), check_object_type):
                        for check_function in check_functions:
                            if skip is not None and check_function.__name__ in skip:
                                continue
                            output = check_function(nwbfile_object)
                            if output is None:
                                continue
                            check_results.append(output)
    return check_results


if __name__ == "__main__":
    main()
