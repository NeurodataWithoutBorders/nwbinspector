"""Primary functions for inspecting NWBFiles."""
import os
import importlib
import traceback
import json
import jsonschema
from pathlib import Path
from collections import Iterable
from enum import Enum
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import FunctionType

import click
import pynwb
import yaml

from . import available_checks
from .inspector_tools import (
    organize_messages,
    format_organized_results_output,
    print_to_console,
    save_report,
)
from .register_checks import InspectorMessage, Importance
from .utils import FilePathType, PathType, OptionalListOfStrings

INTERNAL_CONFIGS = dict(dandi=Path(__file__).parent / "internal_configs" / "dandi.inspector_config.yaml")


class InspectorOutputJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for the NWBInspector."""

    def default(self, o):
        if isinstance(o, InspectorMessage):
            return o.__dict__
        if isinstance(o, Enum):
            return o.name
        else:
            return super().default(o)


def validate_config(config: dict):
    """Validate an instance of configuration against the official schema."""
    with open(file=Path(__file__).parent / "config.schema.json", mode="r") as fp:
        schema = json.load(fp=fp)
    jsonschema.validate(instance=config, schema=schema)


def copy_function(function):
    """
    Return a copy of a function so that internal attributes can be adjusted without changing the original function.

    Required to ensure our configuration of functions in the registry does not effect the registry itself.

    Taken from
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python/30714299#30714299
    """
    if getattr(function, "__wrapped__", False):
        function = function.__wrapped__
    copied_function = FunctionType(
        function.__code__, function.__globals__, function.__name__, function.__defaults__, function.__closure__
    )
    # in case f was given attrs (note this dict is a shallow copy):
    copied_function.__dict__.update(function.__dict__)
    return copied_function


def configure_checks(
    checks: list = available_checks,
    config: Optional[dict] = None,
    ignore: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
) -> list:
    """
    Filter a list of check functions (the entire base registry by default) according to the configuration.

    Parameters
    ----------
    config : dict
        Dictionary valid against our JSON configuration schema.
        Can specify a mapping of importance levels and list of check functions whose importance you wish to change.
        Typically loaded via json.load from a valid .json file
    checks : list of check functions
        Defaults to all registered checks.
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
        If loading all registered checks, this can be shorthand for selecting only a handful of them.
    importance_threshold : string, optional
        Ignores all tests with an post-configuration assigned importance below this threshold.
        Importance has three levels:
            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation
        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    """
    if ignore is not None and select is not None:
        raise ValueError("Options 'ignore' and 'select' cannot both be used.")
    if importance_threshold not in Importance:
        raise ValueError(
            f"Indicated importance_threshold ({importance_threshold}) is not a valid importance level! Please choose "
            "from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION]."
        )
    if config is not None:
        validate_config(config=config)
        checks_out = []
        ignore = ignore or []
        for check in checks:
            mapped_check = copy_function(check)
            for importance_name, func_names in config.items():
                if check.__name__ in func_names:
                    if importance_name == "SKIP":
                        ignore.append(check.__name__)
                        continue
                    mapped_check.importance = Importance[importance_name]
            checks_out.append(mapped_check)
    else:
        checks_out = checks
    if select:
        checks_out = [x for x in checks_out if x.__name__ in select]
    elif ignore:
        checks_out = [x for x in checks_out if x.__name__ not in ignore]
    if importance_threshold:
        checks_out = [x for x in checks_out if x.importance.value >= importance_threshold.value]
    return checks_out


@click.command()
@click.argument("path")
@click.option("-m", "--modules", help="Modules to import prior to reading the file(s).")
@click.option("--no-color", help="Disable coloration for console display of output.", is_flag=True)
@click.option(
    "--report-file-path",
    default=None,
    help="Save path for the report file.",
    type=click.Path(writable=True),
)
@click.option("-o", "--overwrite", help="Overwrite an existing report file at the location.", is_flag=True)
@click.option("-i", "--ignore", help="Comma-separated names of checks to skip.")
@click.option("-s", "--select", help="Comma-separated names of checks to run.")
@click.option(
    "-t",
    "--threshold",
    default="BEST_PRACTICE_SUGGESTION",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    help="Ignores tests with an assigned importance below this threshold.",
)
@click.option(
    "-c", "--config", help="Name of config or path of config .yaml file that overwrites importance of " "checks."
)
@click.option("-j", "--json-file-path", help="Write json output to this location.")
@click.option("--n-jobs", help="Number of jobs to use in parallel.", default=1)
def inspect_all_cli(
    path: str,
    modules: Optional[str] = None,
    no_color: bool = False,
    report_file_path: str = None,
    overwrite: bool = False,
    ignore: Optional[str] = None,
    select: Optional[str] = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
    config: Optional[str] = None,
    json_file_path: Optional[str] = None,
    n_jobs: int = 1,
):
    """Primary CLI usage of the NWBInspector."""
    if config is not None:
        config = INTERNAL_CONFIGS.get(config, config)
        with open(file=config, mode="r") as stream:
            config = yaml.load(stream=stream, Loader=yaml.Loader)
    else:
        config = None
    messages = list(
        inspect_all(
            path=path,
            modules=modules,
            config=config,
            ignore=ignore if ignore is None else ignore.split(","),
            select=select if select is None else select.split(","),
            importance_threshold=Importance[threshold],
            n_jobs=n_jobs,
        )
    )
    if json_file_path is not None:
        with open(file=json_file_path, mode="w") as fp:
            json.dump(obj=messages, fp=fp, cls=InspectorOutputJSONEncoder)
    if len(messages):
        organized_results = organize_messages(messages=messages, levels=["file_path", "importance"])
        formatted_results = format_organized_results_output(organized_results=organized_results)
        print_to_console(formatted_results=formatted_results, no_color=no_color)
        if report_file_path is not None:
            save_report(report_file_path=report_file_path, formatted_results=formatted_results, overwrite=overwrite)
            print(f"{os.linesep*2}Report saved to {str(Path(report_file_path).absolute())}!{os.linesep}")


def inspect_all(
    path: PathType,
    modules: OptionalListOfStrings = None,
    config: dict = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
    n_jobs: int = 1,
):
    """
    Inspect a NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    path : PathType
        File path to an NWBFile, or folder path to iterate over recursively and scan all NWBFiles present.
    modules : list of strings, optional
        List of external module names to load; examples would be namespace extensions.
        These modules may also contain their own custom checks for their extensions.
    config : dict
        Dictionary valid against our JSON configuration schema.
        Can specify a mapping of importance levels and list of check functions whose importance you wish to change.
        Typically loaded via json.load from a valid .json file
    ignore: list of strings, optional
        Names of functions to skip.
    select: list of strings, optional
        Names of functions to pick out of available checks.
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
    n_jobs : int = 1
        Number of jobs to use in parallel. Set to -1 to use all available resources.
        Set to 1 (also the default) to disable.
    """
    modules = modules or []
    path = Path(path)

    in_path = Path(path)
    if in_path.is_dir():
        nwbfiles = list(in_path.rglob("*.nwb"))
    elif in_path.is_file():
        nwbfiles = [in_path]
    else:
        raise ValueError(f"{in_path} should be a directory or an NWB file.")
    for module in modules:
        importlib.import_module(module)
    # Filtering of checks should apply after external modules are imported, in case those modules have their own checks
    checks = configure_checks(config=config, ignore=ignore, select=select, importance_threshold=importance_threshold)

    if n_jobs != 1:

        # max_workers for threading is a different concept to number of processes; from the documentation
        # https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
        # we can multiply the specified number of jobs by 5
        if n_jobs != -1:
            max_workers = n_jobs * 5
        else:
            max_workers = None  # concurrents doesn't have a -1 flag like joblib; set to None to achieve this
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for nwbfile_path in nwbfiles:
                futures.append(executor.submit(inspect_nwb, nwbfile_path=nwbfile_path, checks=checks))
            for future in as_completed(futures):
                for message in future.result():
                    yield message
    else:
        for nwbfile_path in nwbfiles:
            for message in inspect_nwb(nwbfile_path=nwbfile_path, checks=checks):
                yield message


def inspect_nwb(
    nwbfile_path: FilePathType,
    checks: list = available_checks,
    config: dict = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
    driver: str = None,
) -> List[InspectorMessage]:
    """
    Inspect a NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile_path : FilePathType
        Path to the NWBFile.
    checks : list, optional
        list of checks to run
    config : dict
        Dictionary valid against our JSON configuration schema.
        Can specify a mapping of importance levels and list of check functions whose importance you wish to change.
        Typically loaded via json.load from a valid .json file
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
        Names of functions to pick out of available checks.
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
    driver: str, optional
        Forwarded to h5py.File(). Set to "ros3" for reading from s3 url.
    """
    if any(x is not None for x in [config, ignore, select, importance_threshold]):
        checks = configure_checks(
            checks=checks, config=config, ignore=ignore, select=select, importance_threshold=importance_threshold
        )
    nwbfile_path = str(nwbfile_path)
    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r", load_namespaces=True, driver=driver) as io:
        validation_errors = pynwb.validate(io=io)
        if any(validation_errors):
            for validation_error in validation_errors:
                yield InspectorMessage(
                    message=validation_error.reason,
                    importance=Importance.PYNWB_VALIDATION,
                    check_function_name=validation_error.name,
                    location=validation_error.location,
                    file_path=nwbfile_path,
                )
        try:
            nwbfile = io.read()
        except Exception as ex:
            yield InspectorMessage(
                message=traceback.format_exc(),
                importance=Importance.ERROR,
                check_function_name=f"{type(ex)}: {str(ex)}",
                file_path=nwbfile_path,
            )
        for inspector_message in run_checks(nwbfile, checks=checks):
            inspector_message.file_path = nwbfile_path
            yield inspector_message


def run_checks(nwbfile: pynwb.NWBFile, checks: list):
    """
    Run checks on an open NWBFile object.

    Parameters
    ----------
    nwbfile : NWBFile
    checks : list
    """
    for check_function in checks:
        for nwbfile_object in nwbfile.objects.values():
            if issubclass(type(nwbfile_object), check_function.neurodata_type):
                try:
                    output = check_function(nwbfile_object)
                # if an individual check fails, include it in the report and continue with the inspection
                except Exception:
                    output = InspectorMessage(
                        message=traceback.format_exc(),
                        importance=Importance.ERROR,
                        check_function_name=check_function.__name__,
                    )
                if output is not None:
                    if isinstance(output, Iterable):
                        for x in output:
                            yield x
                    else:
                        yield output


if __name__ == "__main__":
    inspect_all_cli()
