"""Primary functions for inspecting NWBFiles."""

import importlib
import re
import traceback
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable, List, Optional, Union
from warnings import filterwarnings, warn

import pynwb
from natsort import natsorted
from packaging.version import Version
from tqdm import tqdm

from . import available_checks, configure_checks
from ._registration import Importance, InspectorMessage
from .tools import get_s3_urls_and_dandi_paths
from .utils import (
    FilePathType,
    OptionalListOfStrings,
    PathType,
    calculate_number_of_cpu,
    get_package_version,
    robust_s3_read,
)


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
    progress_bar_class: tqdm = tqdm,
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
    progress_bar_class : type of tqdm.tqdm, optional
        The specific child class of tqdm.tqdm to use to make progress bars.
        Defaults to tqdm.tqdm, the most generic parent.
    progress_bar_options : dict, optional
        Dictionary of keyword arguments to pass directly to the progress_bar_class.
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

            # Remove any macOS sidecar files
            nwbfiles = [nwbfile for nwbfile in nwbfiles if not nwbfile.name.startswith("._")]
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
        nwbfiles_iterable = progress_bar_class(nwbfiles_iterable, **progress_bar_options)
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
                nwbfiles_iterable = progress_bar_class(nwbfiles_iterable, **progress_bar_options)
            for future in nwbfiles_iterable:
                for message in future.result():
                    if stream:
                        message.file_path = nwbfiles[message.file_path]
                    yield message
    else:
        for nwbfile_path in nwbfiles_iterable:
            for message in inspect_nwbfile(nwbfile_path=nwbfile_path, checks=checks, driver=driver):
                if stream:
                    message.file_path = nwbfiles[message.file_path]
                yield message


def _pickle_inspect_nwb(
    nwbfile_path: str, checks: list = available_checks, skip_validate: bool = False, driver: Optional[str] = None
):
    """Auxiliary function for inspect_all to run in parallel using the ProcessPoolExecutor."""
    return list(inspect_nwbfile(nwbfile_path=nwbfile_path, checks=checks, skip_validate=skip_validate, driver=driver))


# TODO: remove after 7/1/2023
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
) -> Iterable[InspectorMessage]:
    warn(
        "The API function 'inspect_nwb' has been deprecated and will be removed in a future release! "
        "To remove ambiguity, please call either "
        "'inspect_nwbfile' giving a path to the unopened file on a system, or "
        "'inspect_nwbfile_object' passing an already open pynwb.NWBFile object.",
        category=DeprecationWarning,
        stacklevel=2,
    )
    for inspector_message in inspect_nwbfile(
        nwbfile_path=nwbfile_path,
        checks=checks,
        config=config,
        ignore=ignore,
        select=select,
        importance_threshold=importance_threshold,
        driver=driver,
        skip_validate=skip_validate,
        max_retries=max_retries,
    ):
        yield inspector_message


def inspect_nwbfile(
    nwbfile_path: FilePathType,
    driver: Optional[str] = None,
    skip_validate: bool = False,
    max_retries: int = 10,
    checks: list = available_checks,
    config: dict = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
) -> Iterable[InspectorMessage]:
    """
    Open an NWB file, inspect the contents, and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile_path : FilePathType
        Path to the NWB file on disk or on S3.
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
    checks : list, optional
        List of checks to run.
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
    """
    nwbfile_path = str(nwbfile_path)
    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")

    if not skip_validate and get_package_version("pynwb") >= Version("2.2.0"):
        validation_error_list, _ = pynwb.validate(paths=[nwbfile_path], driver=driver)
        for validation_namespace_errors in validation_error_list:
            for validation_error in validation_namespace_errors:
                yield InspectorMessage(
                    message=validation_error.reason,
                    importance=Importance.PYNWB_VALIDATION,
                    check_function_name=validation_error.name,
                    location=validation_error.location,
                    file_path=nwbfile_path,
                )

    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r", load_namespaces=True, driver=driver) as io:
        if not skip_validate and get_package_version("pynwb") < Version("2.2.0"):
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
            in_memory_nwbfile = robust_s3_read(command=io.read, max_retries=max_retries)

            for inspector_message in inspect_nwbfile_object(
                nwbfile_object=in_memory_nwbfile,
                checks=checks,
                config=config,
                ignore=ignore,
                select=select,
                importance_threshold=importance_threshold,
            ):
                inspector_message.file_path = nwbfile_path
                yield inspector_message
        except Exception as ex:
            yield InspectorMessage(
                message=traceback.format_exc(),
                importance=Importance.ERROR,
                check_function_name=f"During io.read() - {type(ex)}: {str(ex)}",
                file_path=nwbfile_path,
            )


# TODO: deprecate once subject types and dandi schemas have been extended
def _intercept_in_vitro_protein(nwbfile_object: pynwb.NWBFile, checks: Optional[list] = None) -> List[callable]:
    """
    If the special 'protein' subject_id is specified, return a truncated list of checks to run.

    This is a temporary method for allowing upload of certain in vitro data to DANDI and
    is expected to replaced in future versions.
    """
    subject_related_check_names = [
        "check_subject_exists",
        "check_subject_id_exists",
        "check_subject_sex",
        "check_subject_species_exists",
        "check_subject_species_form",
        "check_subject_age",
        "check_subject_proper_age_range",
    ]
    subject_related_dandi_requirements = [
        check.importance == Importance.CRITICAL for check in checks if check.__name__ in subject_related_check_names
    ]

    subject = getattr(nwbfile_object, "subject", None)
    if (
        any(subject_related_dandi_requirements)
        and subject is not None
        and (getattr(subject, "subject_id") or "").startswith("protein")
    ):
        non_subject_checks = [check for check in checks if check.__name__ not in subject_related_check_names]
        return non_subject_checks
    return checks


def inspect_nwbfile_object(
    nwbfile_object: pynwb.NWBFile,
    checks: Optional[list] = None,
    config: Optional[dict] = None,
    ignore: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
) -> List[InspectorMessage]:
    """
    Inspect an in-memory NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile_object : NWBFile
        An in-memory NWBFile object.
    checks : list, optional
        list of checks to run
    config : dict, optional
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
    """
    checks = checks or available_checks
    importance_threshold = (
        Importance[importance_threshold] if isinstance(importance_threshold, str) else importance_threshold
    )
    if any(argument is not None for argument in [config, ignore, select, importance_threshold]):
        checks = configure_checks(
            checks=checks, config=config, ignore=ignore, select=select, importance_threshold=importance_threshold
        )

    subject_dependent_checks = _intercept_in_vitro_protein(nwbfile_object=nwbfile_object, checks=checks)

    for inspector_message in run_checks(nwbfile=nwbfile_object, checks=subject_dependent_checks):
        yield inspector_message


def run_checks(
    nwbfile: pynwb.NWBFile,
    checks: list,
    progress_bar_class: Optional[tqdm] = None,
    progress_bar_options: Optional[dict] = None,
) -> Iterable[InspectorMessage]:
    """
    Run checks on an open NWBFile object.

    Parameters
    ----------
    nwbfile : pynwb.NWBFile
        The in-memory pynwb.NWBFile object to run the checks on.
    checks : list of check functions
        The list of check functions that will be run on the in-memory pynwb.NWBFile object.
    progress_bar_class : type of tqdm.tqdm, optional
        The specific child class of tqdm.tqdm to use to make progress bars.
        Defaults to not displaying progress per set of checks over an invidiual file.
    progress_bar_options : dict, optional
        Dictionary of keyword arguments to pass directly to the `progress_bar_class`.

    Yields
    ------
    results : a generator of InspectorMessage objects
        A generator that returns a message on each iteration, if any are triggered by downstream conditions.
        Otherwise, has length zero (if cast as `list`), or raises `StopIteration` (if explicitly calling `next`).
    """
    if progress_bar_class is not None:
        check_progress = progress_bar_class(iterable=checks, total=len(checks), **progress_bar_options)
    else:
        check_progress = checks

    for check_function in check_progress:
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
                if isinstance(output, InspectorMessage):
                    # temporary solution to https://github.com/dandi/dandi-cli/issues/1031
                    if output.importance != Importance.ERROR:
                        output.importance = check_function.importance
                    yield output
                elif output is not None:
                    for x in output:
                        x.importance = check_function.importance
                        yield x


if __name__ == "__main__":
    inspect_all_cli()
