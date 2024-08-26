"""Primary functions for inspecting NWBFiles."""

import os
import re
import json
import warnings
from pathlib import Path
from typing import Union, Literal

import click

from ._formatting import _get_report_header
from . import Importance, inspect_all, format_messages, print_to_console, save_report, __version__
from .utils import strtobool
from ._dandi_inspection import inspect_dandiset, inspect_dandi_file_path, insect_dandi_s3_url


@click.command()
@click.argument("path", nargs=1)
@click.option(
    "--stream",
    help="Whether or not to stream file content from the DANDI archive. Automatically enabled if path is a URL.",
    is_flag=True,
    required=False,
    default=False,
)
@click.option(
    "--version-id",
    help="The version ID of the Dandiset to inspect. Defaults to 'draft' if '--stream' is specified.",
    type=str,
    required=False,
    default=None,
)
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
@click.option(
    "--config",
    help="Name of internal config or path to a custom YAML file.",
    type=str,
    required=False,
    default="dandi",
)
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
    "--modules",
    help="Modules to import prior to reading the file(s). Necessary for registration of custom checks functions.",
    type=str,
    required=False,
    default=None,
)
@click.version_option(__version__)
def _nwbinspector_cli(
    path: str,
    /,
    *,
    stream: bool = False,
    version_id: Union[str, None] = None,
    report_file_path: str = None,
    levels: str = None,
    reverse: Union[str, None] = None,
    overwrite: bool = False,
    ignore: Union[str, None] = None,
    select: Union[str, None] = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
    config: str = "dandi",
    json_file_path: Union[str, None] = None,
    n_jobs: int = 1,
    skip_validate: bool = False,
    detailed: bool = False,
    progress_bar: Union[str, None] = None,
    modules: Union[str, None] = None,
) -> None:
    """
    Run the NWB Inspector via the command line.

    Example Usage
    -------------
    nwbinspector path/to/folder

    nwbinspector path/to/file.nwb

    nwbinspector 000003 --stream

    nwbinspector 000003:sub-YutaMouse39/sub-YutaMouse39_ses-YutaMouse39-150727_behavior+ecephys.nwb  \
      --stream --version-id draft
    """
    path_is_url = path.startswith("https://")
    stream = True if path_is_url else stream

    if stream is True and config != "dandi":
        message = (
            "File content originates from DANDI, but a custom config was specified. "
            "The 'dandi' config will be used instead."
        )
        raise ValueError(message)

    dandiset_version = "draft" if stream is True and version_id is None else version_id
    handled_levels = ["importance", "file_path"] if levels is None else levels.split(",")
    handled_reverse = [False] * len(levels) if reverse is None else [strtobool(x) for x in reverse.split(",")]
    handled_ignore = ignore if ignore is None else ignore.split(",")
    handled_select = select if select is None else select.split(",")
    handled_importance_threshold = Importance[threshold]
    config = load_config(filepath_or_keyword=config)
    show_progress_bar = True if progress_bar is None else strtobool(progress_bar)
    modules = [] if modules is None else modules.split(",")

    # Trigger the import of custom checks that have been registered and exposed to their respective modules
    for module in modules:
        importlib.import_module(name=module)

    # Scan entire Dandiset
    if stream is True and ":" not in path:
        dandiset_id = path
        messages_iterator = inspect_dandiset(
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            config=config,
            ignore=handled_ignore,
            select=handled_select,
            importance_threshold=handled_importance_threshold,
            skip_validate=skip_validate,
            show_progress_bar=show_progress_bar,
        )
    # Scan a single NWB file in a Dandiset
    elif stream is True and ":" in path:
        dandiset_id, dandi_file_path = path.split(":")
        messages_iterator = inspect_dandi_file_path(
            dandi_file_path=dandi_file_path,
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            config=config,
            ignore=handled_ignore,
            select=handled_select,
            importance_threshold=handled_importance_threshold,
            skip_validate=skip_validate,
        )
    # Scan single NWB file at URL
    elif stream is True and path_is_url is True:
        dandi_s3_url = path
        messages_iterator = insect_dandi_s3_url(
            dandi_s3_url=dandi_s3_url,
            config=config,
            ignore=handled_ignore,
            select=handled_select,
            importance_threshold=handled_importance_threshold,
            skip_validate=skip_validate,
        )
    # Scan local file/folder
    elif stream is False:
        messages_iterator = inspect_all(
            path=path,
            config=config,
            ignore=handled_ignore,
            select=handled_select,
            importance_threshold=handled_importance_threshold,
            n_jobs=n_jobs,
            skip_validate=skip_validate,
            progress_bar=show_progress_bar,
        )
    messages = list(messages_iterator)

    if json_file_path is not None:
        if Path(json_file_path).exists() and not overwrite:
            raise FileExistsError(f"The file {json_file_path} already exists! Specify the '-o' flag to overwrite.")
        with open(file=json_file_path, mode="w") as fp:
            json_report = dict(header=_get_report_header(), messages=messages)
            json.dump(obj=json_report, fp=fp, cls=InspectorOutputJSONEncoder)
            print(f"{os.linesep*2}Report saved to {str(Path(json_file_path).absolute())}!{os.linesep}")

    formatted_messages = format_messages(
        messages=messages, levels=handled_levels, reverse=handled_reverse, detailed=detailed
    )
    print_to_console(formatted_messages=formatted_messages)
    if report_file_path is not None:
        save_report(report_file_path=report_file_path, formatted_messages=formatted_messages, overwrite=overwrite)
        print(f"{os.linesep*2}Report saved to {str(Path(report_file_path).absolute())}!{os.linesep}")
