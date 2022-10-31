"""Primary functions for inspecting NWBFiles."""
import os
import re
import importlib
import traceback
import json
import jsonschema
from pathlib import Path
from collections.abc import Iterable
from enum import Enum
from typing import Union, Optional, List
from concurrent.futures import ProcessPoolExecutor, as_completed
from types import FunctionType
from warnings import filterwarnings, warn
from distutils.util import strtobool
from collections import defaultdict

import click
import pynwb
import yaml
from tqdm import tqdm
from natsort import natsorted

from . import available_checks
from .inspector_tools import (
    get_report_header,
    format_messages,
    print_to_console,
    save_report,
)
from .register_checks import InspectorMessage, Importance
from .tools import get_s3_urls_and_dandi_paths
from .utils import FilePathType, PathType, OptionalListOfStrings, robust_s3_read, calculate_number_of_cpu

INTERNAL_CONFIGS = dict(dandi=Path(__file__).parent / "internal_configs" / "dandi.inspector_config.yaml")


class InspectorOutputJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for the NWBInspector."""

    def default(self, o):  # noqa D102
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


def _copy_function(function):
    """
    Copy the core parts of a given function, excluding wrappers, then return a new function.

    Based off of
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python/30714299#30714299
    """
    copied_function = FunctionType(
        function.__code__, function.__globals__, function.__name__, function.__defaults__, function.__closure__
    )

    # in case f was given attrs (note this dict is a shallow copy)
    copied_function.__dict__.update(function.__dict__)
    return copied_function


def copy_check(function):
    """
    Copy a check function so that internal attributes can be adjusted without changing the original function.

    Required to ensure our configuration of functions in the registry does not effect the registry itself.

    Also copies the wrapper for auto-parsing results,
    see https://github.com/NeurodataWithoutBorders/nwbinspector/pull/218 for explanation.

    Taken from
    https://stackoverflow.com/questions/6527633/how-can-i-make-a-deepcopy-of-a-function-in-python/30714299#30714299
    """
    if getattr(function, "__wrapped__", False):
        check_function = function.__wrapped__
    copied_function = _copy_function(function)
    copied_function.__wrapped__ = _copy_function(check_function)
    return copied_function


def load_config(filepath_or_keyword: PathType) -> dict:
    """
    Load a config dictionary either via keyword search of the internal configs, or an explicit filepath.

    Currently supported keywords are:
        - 'dandi'
            For all DANDI archive related practices, including validation and upload.
    """
    file = INTERNAL_CONFIGS.get(filepath_or_keyword, filepath_or_keyword)
    with open(file=file, mode="r") as stream:
        config = yaml.load(stream=stream, Loader=yaml.Loader)
    return config


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
            mapped_check = copy_check(check)
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
@click.option("--modules", help="Modules to import prior to reading the file(s).")
@click.option(
    "--report-file-path",
    default=None,
    help="Save path for the report file.",
    type=click.Path(writable=True),
)
@click.option("--overwrite", help="Overwrite an existing report file at the location.", is_flag=True)
@click.option("--levels", help="Comma-separated names of InspectorMessage attributes to organize by.")
@click.option(
    "--reverse", help="Comma-separated booleans corresponding to reversing the order for each value of 'levels'."
)
@click.option("--ignore", help="Comma-separated names of checks to skip.")
@click.option("--select", help="Comma-separated names of checks to run.")
@click.option(
    "--threshold",
    default="BEST_PRACTICE_SUGGESTION",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    help="Ignores tests with an assigned importance below this threshold.",
)
@click.option("--config", help="Name of config or path of config .yaml file that overwrites importance of checks.")
@click.option("--json-file-path", help="Write json output to this location.")
@click.option("--n-jobs", help="Number of jobs to use in parallel.", default=1)
@click.option("--skip-validate", help="Skip the PyNWB validation step.", is_flag=True)
@click.option(
    "--detailed",
    help=(
        "If file_path is the last of 'levels' (the default), identical checks will be aggregated in the display. "
        "Use '--detailed' to see the complete report."
    ),
    is_flag=True,
)
@click.option("--progress-bar", help="Set this flag to False to disable display of the progress bar.")
@click.option(
    "--stream",
    help=(
        "Stream data from the DANDI archive. If the 'path' is a local copy of the target DANDISet, specifying this "
        "flag will still force the data to be streamed instead of using the local copy. To use the local copy, simply "
        "remove this flag. Requires the Read Only S3 (ros3) driver to be installed with h5py."
    ),
    is_flag=True,
)
@click.option(
    "--version-id",
    help=(
        "When 'path' is a six-digit DANDISet ID, this further specifies which version of " "the DANDISet to inspect."
    ),
)
def inspect_all_cli(
    path: str,
    modules: Optional[str] = None,
    report_file_path: str = None,
    levels: str = None,
    reverse: Optional[str] = None,
    overwrite: bool = False,
    ignore: Optional[str] = None,
    select: Optional[str] = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
    config: Optional[str] = None,
    json_file_path: Optional[str] = None,
    n_jobs: int = 1,
    skip_validate: bool = False,
    detailed: bool = False,
    progress_bar: Optional[str] = None,
    stream: bool = False,
    version_id: Optional[str] = None,
):
    """
    Run the NWBInspector via the command line.

    path :
    Path to either a local NWBFile, a local folder containing NWBFiles, a link to a dataset on
    DANDI archive (i.e., https://dandiarchive.org/dandiset/{dandiset_id}/{version_id}), or a six-digit Dandiset ID.
    """
    levels = ["importance", "file_path"] if levels is None else levels.split(",")
    reverse = [False] * len(levels) if reverse is None else [strtobool(x) for x in reverse.split(",")]
    progress_bar = strtobool(progress_bar) if progress_bar is not None else True
    if config is not None:
        config = load_config(filepath_or_keyword=config)
    if stream:
        url_path = path if path.startswith("https://") else None
        if url_path:
            dandiset_id, version_id = url_path.split("/")[-2:]
            path = dandiset_id
        assert url_path or re.fullmatch(
            pattern="^[0-9]{6}$", string=path
        ), "'--stream' flag was enabled, but 'path' is neither a full link to the DANDI archive nor a DANDISet ID."
        if Path(path).is_dir():
            warn(
                f"The local DANDISet '{path}' exists, but the '--stream' flag was used. "
                "NWBInspector will use S3 streaming from DANDI. To use local data, remove the '--stream' flag."
            )
    messages = list(
        inspect_all(
            path=path,
            modules=modules,
            ignore=ignore if ignore is None else ignore.split(","),
            select=select if select is None else select.split(","),
            importance_threshold=Importance[threshold],
            config=config,
            n_jobs=n_jobs,
            skip_validate=skip_validate,
            progress_bar=progress_bar,
            stream=stream,
            version_id=version_id,
        )
    )
    if json_file_path is not None:
        if Path(json_file_path).exists() and not overwrite:
            raise FileExistsError(f"The file {json_file_path} already exists! Specify the '-o' flag to overwrite.")
        with open(file=json_file_path, mode="w") as fp:
            json_report = dict(header=get_report_header(), messages=messages)
            json.dump(obj=json_report, fp=fp, cls=InspectorOutputJSONEncoder)
            print(f"{os.linesep*2}Report saved to {str(Path(json_file_path).absolute())}!{os.linesep}")
    formatted_messages = format_messages(messages=messages, levels=levels, reverse=reverse, detailed=detailed)
    print_to_console(formatted_messages=formatted_messages)
    if report_file_path is not None:
        save_report(report_file_path=report_file_path, formatted_messages=formatted_messages, overwrite=overwrite)
        print(f"{os.linesep*2}Report saved to {str(Path(report_file_path).absolute())}!{os.linesep}")


def inspect_all(
    path: PathType,
    modules: OptionalListOfStrings = None,
    config: Optional[dict] = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
    n_jobs: int = 1,
    skip_validate: bool = False,
    progress_bar: bool = True,
    progress_bar_options: Optional[dict] = None,
    stream: bool = False,
    version_id: Optional[str] = None,
):
    """
    Inspect a local NWBFile or folder of NWBFiles and return suggestions for improvements according to best practices.

    Parameters
    ----------
    path : PathType
        File path to an NWBFile, folder path to iterate over recursively and scan all NWBFiles present, or a
        six-digit identifier of the DANDISet.
    modules : list of strings, optional
        List of external module names to load; examples would be namespace extensions.
        These modules may also contain their own custom checks for their extensions.
    config : dict, optional
        If a dictionary, it must be valid against our JSON configuration schema.
        Can specify a mapping of importance levels and list of check functions whose importance you wish to change.
        Typically loaded via json.load from a valid .json file
    ignore: list of strings, optional
        Names of functions to skip.
    select: list of strings, optional
        Names of functions to pick out of available checks.
    importance_threshold : string or Importance, optional
        Ignores tests with an assigned importance below this threshold.
        Importance has three levels:

            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation

        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    n_jobs : int
        Number of jobs to use in parallel. Set to -1 to use all available resources.
        This may also be a negative integer x from -2 to -(number_of_cpus - 1) which acts like negative slicing by using
        all available CPUs minus x.
        Set to 1 (also the default) to disable.
    skip_validate : bool, optional
        Skip the PyNWB validation step. This may be desired for older NWBFiles (< schema version v2.10).
        The default is False, which is also recommended.
    progress_bar : bool, optional
        Display a progress bar while scanning NWBFiles.
        Defaults to True.
    progress_bar_options : dict, optional
        Dictionary of keyword arguments to pass directly to tqdm.
    stream : bool, optional
        Stream data from the DANDI archive. If the 'path' is a local copy of the target DANDISet, setting this
        argument to True will force the data to be streamed instead of using the local copy.
        Requires the Read Only S3 (ros3) driver to be installed with h5py.
        Defaults to False.
    version_id : str, optional
        If the path is a DANDISet ID, version_id additionally specifies which version of the dataset to read from.
        Common options are 'draft' or 'published'.
        Defaults to the most recent published version, or if not published then the most recent draft version.
    """
    importance_threshold = (
        Importance[importance_threshold] if isinstance(importance_threshold, str) else importance_threshold
    )
    modules = modules or []
    n_jobs = calculate_number_of_cpu(requested_cpu=n_jobs)
    if progress_bar_options is None:
        progress_bar_options = dict(position=0, leave=False)
        if stream:
            progress_bar_options.update(desc="Inspecting NWBFiles with ROS3...")
        else:
            progress_bar_options.update(desc="Inspecting NWBFiles...")
    if stream:
        assert (
            re.fullmatch(pattern="^[0-9]{6}$", string=str(path)) is not None
        ), "'--stream' flag was enabled, but 'path' is not a DANDISet ID."
        driver = "ros3"
        nwbfiles = get_s3_urls_and_dandi_paths(dandiset_id=path, version_id=version_id, n_jobs=n_jobs)
    else:
        driver = None
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

    # Manual identifier check over all files in the folder path
    identifiers = defaultdict(list)
    for nwbfile_path in nwbfiles:
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r", load_namespaces=True, driver=driver) as io:
            nwbfile = robust_s3_read(io.read)
            identifiers[nwbfile.identifier].append(nwbfile_path)
    if len(identifiers) != len(nwbfiles):
        for identifier, nwbfiles_with_identifier in identifiers.items():
            if len(nwbfiles_with_identifier) > 1:
                yield InspectorMessage(
                    message=(
                        f"The identifier '{identifier}' is used across the .nwb files: "
                        f"{natsorted([x.name for x in nwbfiles_with_identifier])}. "
                        "The identifier of any NWBFile should be a completely unique value - "
                        "we recommend using uuid4 to achieve this."
                    ),
                    importance=Importance.CRITICAL,
                    check_function_name="check_unique_identifiers",
                    object_type="NWBFile",
                    object_name="root",
                    location="/",
                    file_path=str(path),
                )

    nwbfiles_iterable = nwbfiles
    if progress_bar:
        nwbfiles_iterable = tqdm(nwbfiles_iterable, **progress_bar_options)
    if n_jobs != 1:
        progress_bar_options.update(total=len(nwbfiles))
        futures = []
        n_jobs = None if n_jobs == -1 else n_jobs  # concurrents uses None instead of -1 for 'auto' mode
        with ProcessPoolExecutor(max_workers=n_jobs) as executor:
            for nwbfile_path in nwbfiles:
                futures.append(
                    executor.submit(
                        _pickle_inspect_nwb,
                        nwbfile_path=nwbfile_path,
                        checks=checks,
                        skip_validate=skip_validate,
                        driver=driver,
                    )
                )
            nwbfiles_iterable = as_completed(futures)
            if progress_bar:
                nwbfiles_iterable = tqdm(nwbfiles_iterable, **progress_bar_options)
            for future in nwbfiles_iterable:
                for message in future.result():
                    if stream:
                        message.file_path = nwbfiles[message.file_path]
                    yield message
    else:
        for nwbfile_path in nwbfiles_iterable:
            for message in inspect_nwb(nwbfile_path=nwbfile_path, checks=checks, driver=driver):
                if stream:
                    message.file_path = nwbfiles[message.file_path]
                yield message


def _pickle_inspect_nwb(
    nwbfile_path: str, checks: list = available_checks, skip_validate: bool = False, driver: Optional[str] = None
):
    """Auxiliary function for inspect_all to run in parallel using the ProcessPoolExecutor."""
    return list(inspect_nwb(nwbfile_path=nwbfile_path, checks=checks, skip_validate=skip_validate, driver=driver))


def inspect_nwb(
    nwbfile_path: FilePathType,
    checks: list = available_checks,
    config: dict = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
    driver: Optional[str] = None,
    skip_validate: bool = False,
    max_retries: int = 10,
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
    importance_threshold : string or Importance, optional
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
    skip_validate : bool
        Skip the PyNWB validation step. This may be desired for older NWBFiles (< schema version v2.10).
        The default is False, which is also recommended.
    max_retries : int, optional
        When using the ros3 driver to stream data from an s3 path, occasional curl issues can result.
        AWS suggests using iterative retry with an exponential backoff of 0.1 * 2^retries.
        This sets a hard bound on the number of times to attempt to retry the collection of messages.
        Defaults to 10 (corresponds to 102.4s maximum delay on final attempt).
    """
    importance_threshold = (
        Importance[importance_threshold] if isinstance(importance_threshold, str) else importance_threshold
    )
    if any(x is not None for x in [config, ignore, select, importance_threshold]):
        checks = configure_checks(
            checks=checks, config=config, ignore=ignore, select=select, importance_threshold=importance_threshold
        )
    nwbfile_path = str(nwbfile_path)
    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")

    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r", load_namespaces=True, driver=driver) as io:
        if not skip_validate:
            validation_errors = pynwb.validate(io=io)
            for validation_error in validation_errors:
                yield InspectorMessage(
                    message=validation_error.reason,
                    importance=Importance.PYNWB_VALIDATION,
                    check_function_name=validation_error.name,
                    location=validation_error.location,
                    file_path=nwbfile_path,
                )

        try:
            nwbfile = robust_s3_read(command=io.read, max_retries=max_retries)
            for inspector_message in run_checks(nwbfile=nwbfile, checks=checks):
                inspector_message.file_path = nwbfile_path
                yield inspector_message
        except Exception as ex:
            yield InspectorMessage(
                message=traceback.format_exc(),
                importance=Importance.ERROR,
                check_function_name=f"During io.read() - {type(ex)}: {str(ex)}",
                file_path=nwbfile_path,
            )


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
            if check_function.neurodata_type is None or issubclass(type(nwbfile_object), check_function.neurodata_type):
                try:
                    output = robust_s3_read(command=check_function, command_args=[nwbfile_object])
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
