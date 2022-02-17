"""Primary functions for inspecting NWBFiles."""
import os
import importlib
import traceback
from pathlib import Path
from collections import OrderedDict, Iterable

import click

import pynwb
from natsort import natsorted

from . import available_checks, Importance
from .inspector_tools import organize_check_results, write_results, print_to_console
from .utils import FilePathType, PathType, OptionalListOfStrings


@click.command()
@click.argument("path")
@click.option("-m", "--modules", help="Modules to import prior to reading the file(s).")
@click.option("-o", "--overwrite", help="Overwrite an existing log file at the location.", is_flag=True)
@click.option(
    "--log-file-path",
    default="nwbinspector_log_file.txt",
    help="Save path for the log file. Defaults to the current directory.",
    type=click.Path(writable=True),
)
@click.option("-i", "--ignore", help="Comma-separated names of checks to skip.")
@click.option("-s", "--select", help="Comma-separated names of checks to run")
@click.option(
    "-t",
    "--threshold",
    default="BEST_PRACTICE_SUGGESTION",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    help="Ignores tests with an assigned importance below this threshold.",
)
def inspect_all_cli(
    path: str,
    modules: OptionalListOfStrings = None,
    log_file_path: str = "nwbinspector_log_file.txt",
    overwrite: bool = False,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
):
    """Primary CLI usage."""
    inspect_all(
        path,
        modules=modules,
        log_file_path=log_file_path,
        ignore=ignore if ignore is None else ignore.split(","),
        select=select if select is None else select.split(","),
        importance_threshold=Importance[threshold],
        overwrite=overwrite,
    )


def inspect_all(
    path: PathType,
    modules: OptionalListOfStrings = None,
    log_file_path: FilePathType = "nwbinspector_log_file.txt",
    overwrite=False,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
):
    """Inspect all NWBFiles at the specified path."""
    modules = modules or []
    path = Path(path)
    log_file_path = Path(log_file_path)

    in_path = Path(path)
    if in_path.is_dir():
        nwbfiles = list(in_path.glob("*.nwb"))
    elif in_path.is_file():
        nwbfiles = [in_path]
    else:
        raise ValueError(f"{in_path} should be a directory or an NWB file.")
    nwbfiles = natsorted(nwbfiles)
    num_nwbfiles = len(nwbfiles)

    for module in modules:
        importlib.import_module(module)
    num_invalid_files = 0
    num_exceptions = 0
    organized_results = dict()
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
                    nwbfile=nwbfile,
                    ignore=ignore,
                    select=select,
                    importance_threshold=importance_threshold,
                )
                if any(check_results):
                    organized_results.update({str(nwbfile_path): organize_check_results(check_results=check_results)})
        except Exception as ex:
            num_exceptions += 1
            print("ERROR: ", ex)
            traceback.print_exc()
    if len(organized_results):
        write_results(log_file_path=log_file_path, organized_results=organized_results, overwrite=overwrite)
        print_to_console(log_file_path=log_file_path)
        print(f"{os.linesep*2}Log file saved at {str(log_file_path.absolute())}!")
    if num_invalid_files:
        print(f"{num_exceptions}/{num_nwbfiles} files are invalid.")
    if num_exceptions:
        print(f"{num_exceptions}/{num_nwbfiles} files had errors.")


def inspect_nwb(
    nwbfile: pynwb.NWBFile,
    checks: OrderedDict = available_checks,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
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
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
    """
    if ignore is not None and select is not None:
        raise ValueError("Options 'ignore' and 'select' cannot both be used.")
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
                            if ignore is not None and check_function.__name__ in ignore:
                                continue
                            if select is not None and check_function.__name__ not in select:
                                continue
                            output = check_function(nwbfile_object)
                            if output is not None:
                                if isinstance(output, Iterable):
                                    check_results.extend(output)
                                else:
                                    check_results.append(output)
    return check_results


if __name__ == "__main__":
    inspect_all_cli()
