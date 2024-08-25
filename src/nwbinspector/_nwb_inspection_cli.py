"""Primary functions for inspecting NWBFiles."""

import os
import re
import json
import warnings
from pathlib import Path
from typing import Optional, List, Union

import click

from ._formatting import _get_report_header
from . import Importance, inspect_all, format_messages, print_to_console, save_report, __version__
from .utils import strtobool


@click.command()
@click.argument("input", nargs=-1)
# TODO: fully deprecate these commands after 3/1/2025
@click.option(
    "--report-file-path",
    default=None,
    help="Save path for the report file.",
    type=click.Path(writable=True),
)
@click.option("--overwrite", help="Overwrite an existing report file at the location.", is_flag=True)
@click.option(
    "--threshold",
    default="BEST_PRACTICE_SUGGESTION",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    help="Ignores tests with an assigned importance below this threshold.",
)
@click.option("--json-file-path", help="Write json output to this location.")
@click.option("--n-jobs", help="Number of jobs to use in parallel.", default=1)
@click.option("--skip-validate", help="Skip the PyNWB validation step.", is_flag=True)
@click.option("--progress-bar", help="DEPRECATED: please use `--progress` instead.")
@click.option("--stream", help="DEPRECATED: please use `--dandiset` instead.", is_flag=True)
@click.option("--version-id", help="DEPRECATED: please use `--version` instead.")
# New options with better help
@click.option(
    "--dandiset",
    help="The six-digit ID of the Dandiset to inspect.",
    type=str,
    required=True,
    default=None,
)
@click.option(
    "--dandifile",
    help="The path to the Dandifile as seen on the archive; e.g., 'sub-123_ses-456+ecephys.nwb'.",
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
    "--savepath",
    help="Save path for the report file.",
    type=click.Path(writable=True),
    default=None,
)
@click.option(
    "--format",
    help="The format to use when saving the report.",
    type=click.Choice(["txt", "json"]),
    default="txt",
)
@click.option(
    "--config",
    help="Name of built-in config to use (e.g., 'dandi') or the path of a locally defined YAML config file.",
    type=str,
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
    "--threshold",
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
@click.version_option(__version__)
def _inspect_cli(
    input: Union[str, List[str]],
    /,
    *,
    dandiset: str,
    version: str,
    savepath: str,
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
    modules: Optional[str] = None,
):
    """
    Run the NWB Inspector via the command line.

    Example Usage
    -------------
    nwbinspector path/to/folder

    nwbinspector path/to/file.nwb

    nwbinspector --dandiset 000003

    nwbinspector --dandiset 000003 \
      --dandifile sub-YutaMouse39/sub-YutaMouse39_ses-YutaMouse39-150727_behavior+ecephys.nwb \
      --version 0.230629.1955
    """
    if len(input) == 0 and dandiset is None:  # Using only flags for new --dandiset usage
        message = "If you are not inspecting local paths, please provide the `--dandiset < six-digit ID >` flag."
        raise ValueError(message)
    if len(input) > 1:
        message = "More than one argument passed to NWB Inspector command line. Please provide only one local path."
        raise ValueError(message)
    if len(input) == 1 and not pathlib.Path(input).exists():
        message = f"Path '{input}' does not exist. Please provide a valid path to an NWB file or a folder of NWB files."
        raise FileNotFoundError(message)

    # TODO: hard deprecate these methods after 3/1/2025
    if report_file_path is not None:
        warnings.warn(
            "The '--report-file-path' flag is deprecated and will be removed in a future release. "
            "Please use the '--json-file-path' flag instead."
        )

    # Match one-word CLI arguments to the API for readability (except for comma splits)
    # Also parse items from string-based inputs into their correct Python types
    dandiset_id = dandiset
    dandiset_version = version
    report_file_path = pathlib.Path(savepath) if savepath is not None else None
    as_json_format = JSON
    split_levels = levels.split(",") if levels is not None else ["importance", "file_path"]
    split_reverse = [strtobool(x) for x in reverse.split(",")] if reverse is not None else [False] * len(levels)
    split_ignore = ignore.split(",") if ignore is not None else None
    split_select = select.split(",") if select is not None else None
    importance_threshold = Importance[threshold]
    show_progress_bar = progress
    split_modules = modules.split(",") if modules is not None else []

    return inspect(
        input=input,
        dandiset_id=dandiset_id,
        dandiset_version=dandiset_version,
        report_file_path=report_file_path,
    )
