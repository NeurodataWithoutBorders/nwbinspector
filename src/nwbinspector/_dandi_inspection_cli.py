"""Primary functions for inspecting NWBFiles."""

import os
import re
import json
from pathlib import Path
from typing import Optional, Union
from warnings import warn
import importlib

import click

from ._formatting import _get_report_header, format_messages, print_to_console, save_report
from ._types import Importance
from .utils import strtobool
from ._dandi_inspection import inspect_dandiset, inspect_dandi_file_path


@click.command("--inspect_dandiset")
@click.option(
    "--dandiset",
    help="The six-digit ID of the Dandiset to inspect.",
    type=str,
    required=True,
    default=None,
)
@click.option(
    "---version",
    help="The version of the Dandiset to inspect.",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "--path",
    help="File path specifying where to save the report for future reference.",
    type=click.Path(writable=True),
    required=False,
    default=None,
)
@click.option(
    "--JSON",
    help="Save the report as a JSON file at the specified path. Otherwise, the classic text structure is used.",
    is_flag=True,
    required=False,
    default=None,
)
@click.option(
    "--levels",
    help="Comma-separated names of InspectorMessage attributes to organize by.",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "--reverse",
    help="Comma-separated booleans corresponding to reversing the order for each value of 'levels'.",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "--ignore",
    help="Comma-separated names of checks to skip.",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "--select",
    help="Comma-separated names of checks to run.",
    type=str,
    required=False,
    default=None,
)
@click.option(
    "--importance",
    help="Ignores tests with an assigned importance below this threshold.",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    required=False,
    default="BEST_PRACTICE_SUGGESTION",
)
@click.option(
    "--validate",
    help="Skip the PyNWB validation step.",
    is_flag=True,
    required=False,
    default=True,
)
@click.option(
    "--detailed",
    help=(
        "If file_path is the last of 'levels' (the default), similar checks will be aggregated in the display. "
        "Use `--detailed` to see the complete report."
    ),
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "--progress",
    help="Whether to display a progress bar while scanning the assets on the Dandiset.",
    is_flag=True,
    required=False,
    default=True,
)
@click.option(
    "--modules",
    help="Modules to import prior to reading the file(s). Necessary for registration of custom checks functions.",
    type=str,
    required=False,
    default=None,
)
def _inspect_dandiset_cli(
    *,
    dandiset: str,
    version: str,
    path: str = None,
    JSON: bool = None,
    levels: str = None,
    reverse: Union[str, None] = None,
    ignore: Union[str, None] = None,
    select: Union[str, None] = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
    json_file_path: Union[str, None] = None,
    validate: bool = True,
    detailed: bool = False,
    progress: bool = None,
    modules: Union[str, None] = None,
) -> None:
    """
    Run the `inspect_dandiset` method via the command line.

    Shortens a few argument names for the CLI.

    Always enforces the DANDI config.
    """
    # Match one-word CLI arguments to the API for readability (except for comma splits)
    # Also parse items from string-based inputs into their correct Python types
    dandiset_id = dandiset
    dandiset_version = version
    report_file_path = pathlib.Path(path) if path is not None else None
    as_json_format = JSON
    split_levels = levels.split(",") if levels is not None else ["importance", "file_path"]
    split_reverse = [strtobool(x) for x in reverse.split(",")] if reverse is not None else [False] * len(levels)
    split_ignore = ignore.split(",") if ignore is not None else None
    split_select = select.split(",") if select is not None else None
    importance_threshold = Importance[threshold]
    show_progress_bar = progress
    split_modules = modules.split(",") if modules is not None else []

    for module_name in split_modules:
        importlib.import_module(name=module_name)

    messages = list(
        inspect_dandiset(
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            ignore=split_ignore,
            select=split_select,
            importance_threshold=importance_threshold,
            skip_validate=not validate,
            show_progress_bar=show_progress_bar,
        )
    )

    formatted_messages = format_messages(
        messages=messages, levels=split_levels, reverse=split_reverse, detailed=detailed
    )
    print_to_console(formatted_messages=formatted_messages)

    if path is None:
        return None

    if as_json_format is True:
        with open(file=path, mode="w") as fp:
            json_report = dict(header=_get_report_header(), messages=messages)
            json.dump(obj=json_report, fp=fp, cls=InspectorOutputJSONEncoder)
            print(f"{os.linesep*2}Report saved to {str(Path(json_file_path).absolute())}!{os.linesep}")
    else:
        save_report(report_file_path=path, formatted_messages=formatted_messages, overwrite=True)
        print(f"{os.linesep*2}Report saved to {str(Path(report_file_path).absolute())}!{os.linesep}")

    return None


@click.command("--inspect_dandi_file_path")
@click.option(
    "--dandi_file_path",
    help="The path to the Dandifile as seen on the archive; e.g., 'sub-123_ses-456+ecephys.nwb'.",
    required=True,
    type=str,
)
@click.option("--modules", help="Modules to import prior to reading the file(s).")
@click.option(
    "--report-file-path",
    default=None,
    help="Save path for the report file.",
    type=click.Path(writable=True),
)
@click.option("--levels", help="Comma-separated names of InspectorMessage attributes to organize by.")
@click.option(
    "--reverse", help="Comma-separated booleans corresponding to reversing the order for each value of 'levels'."
)
@click.option("--overwrite", help="Overwrite an existing report file at the location.", is_flag=True)
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
def _inspect_dandi_file_path_cli(
    *,
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
) -> None:
    """
    Run the NWBInspector via the command line.

    path :
    Path to either a local NWBFile, a local folder containing NWBFiles, a link to a dataset on
    DANDI archive (i.e., https://dandiarchive.org/dandiset/{dandiset_id}/{version_id}), or a six-digit Dandiset ID.
    """
    levels = ["importance", "file_path"] if levels is None else levels.split(",")
    modules = [] if modules is None else modules.split(",")
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
            json_report = dict(header=_get_report_header(), messages=messages)
            json.dump(obj=json_report, fp=fp, cls=InspectorOutputJSONEncoder)
            print(f"{os.linesep*2}Report saved to {str(Path(json_file_path).absolute())}!{os.linesep}")
    formatted_messages = format_messages(messages=messages, levels=levels, reverse=reverse, detailed=detailed)
    print_to_console(formatted_messages=formatted_messages)
    if report_file_path is not None:
        save_report(report_file_path=report_file_path, formatted_messages=formatted_messages, overwrite=overwrite)
        print(f"{os.linesep*2}Report saved to {str(Path(report_file_path).absolute())}!{os.linesep}")

    return None
