"""Cody Baker, Ben Dichter, and Ryan Ly."""
import argparse
import importlib
import traceback
import numpy as np
from collections import defaultdict, OrderedDict
from typing import Optional, Union, Dict
from pathlib import Path

import pynwb

from . import available_checks, importance_levels


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
        help="modules to import prior to reading the file(s)",
    )
    parser.add_argument("path", help="path to an NWB file or directory containing NWB files")
    parser.add_argument("-w", "--overwrite", help="overwrite an existing log file at the location", default=False)
    parser.set_defaults(modules=[])
    args = parser.parse_args()

    in_path = Path(args.path)
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
                organized_results = organize_inspect_results(check_results=check_results)
                # log_file_path = in_path / "nwbinspector_log_file_{Path(filename).stem}.txt"
                log_file_path = "C:/Users/Raven/Downloads/auto_test.txt"
                write_results(
                    log_file_path=log_file_path, organized_results=organized_results, overwrite=args.overwrite
                )
                # TODO: perhaps with click, if log file exists, ask user for confirmation to flip overwrite flag
                print(f"Log file saved at {str(log_file_path)}!")
        except Exception as ex:
            num_exceptions += 1
            print("ERROR:", ex)
            traceback.print_exc()

    if num_invalid_files:
        print("%d/%d files are invalid." % (num_exceptions, num_invalid_files))
    if num_exceptions:
        print("%d/%d files had errors." % (num_exceptions, num_exceptions))


def sort_by_descending_severity(check_results: list):
    """Order the dictionaries in the check_list by severity."""
    severities = [check_result["severity"] for check_result in check_results]
    descending_indices = np.argsort(severities)[::-1]
    return [check_results[j] for j in descending_indices]


def organize_inspect_results(check_results: list):
    """Format the list of returned results from checks."""
    organized_results = OrderedDict({importance_level: defaultdict(list) for importance_level in importance_levels})
    for check_result in check_results:
        organized_results[check_result["importance"]].append(check_result)
    for importance_level, check_results in organized_results.items():
        if len(check_results) == 0:
            organized_results.pop(importance_level)
        else:
            organized_results[importance_level] = sort_by_descending_severity(check_results=check_results)
    return organized_results


def write_results(log_file_path: Union[Path, str], organized_results: Dict[str, list], overwrite=False):
    """Write the list of organized check results to a nicely formatted text file."""
    log_file_path = Path(log_file_path)

    if log_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {log_file_path} already exists! Set 'overwrite=True' or pass '-w' flag.")

    nwbfile_index = 1  # TODO
    check_index = 1
    with open(file=log_file_path, mode="w", newline="\n") as file:
        nwbfile_name_string = "NWBFile: xxxxxx.nwb"  # TODO
        file.write(nwbfile_name_string + "\n")
        file.write("" * len(nwbfile_name_string) + "\n")

        for importance_index, (importance_level, check_results) in enumerate(organized_results.items()):
            file.write(f"\n{importance_level}\n")
            file.write("-" * len(importance_level) + "\n")

            for check_result in check_results:
                file.write(
                    f"{nwbfile_index}.{importance_index}.{check_index}   {check_result['object_type']} "
                    "'{check_result['object_name']}' located in 'TODO'\n"  # TODO
                    "        {check_result['check_function_name']}: {check_result['message']}"
                )
                check_index += 1


def inspect_nwb(
    nwbfile: pynwb.NWBFile,
    checks: list = available_checks,
    importance_threshold: str = "BEST_PRACTICE_SUGGESTION",
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
            CRITICAL_IMPORTANCE
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation
        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    skip: list, optional
        Names of functions to skip.
    """
    if importance_threshold not in importance_levels:
        raise ValueError(
            f"Indicated importance_threshold ({importance_threshold}) is not a valid importance level! Please choose "
            "from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION]."
        )

    check_results = list()
    for importance, checks_per_object_type in checks.items():
        if importance_levels[importance] >= importance_levels[importance_threshold]:
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
    return check_results


if __name__ == "__main__":
    main()
