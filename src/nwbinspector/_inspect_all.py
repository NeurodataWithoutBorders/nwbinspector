"""Primary functions for inspecting NWBFiles."""

import os
import re
import json
import warnings
from pathlib import Path
from typing import Optional, List

import click

from ._formatting import _get_report_header
from . import Importance, inspect_all, format_messages, print_to_console, save_report, __version__
from .utils import strtobool


def inspect(
    dandiset_id: str,
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
    The API companion for the command line usage of the NWB Inspector.

    Whereas the command line uses shortened flags for optional arguments, this function uses full names for clarity.

    Parameters
    ----------

    """
    # Parse unnamed input argument to determine mode (maintains backwards compatibility)
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
    report_file_path = pathlib.Path(path) if path is not None else None
    as_json_format = JSON
    split_levels = levels.split(",") if levels is not None else ["importance", "file_path"]
    split_reverse = [strtobool(x) for x in reverse.split(",")] if reverse is not None else [False] * len(levels)
    split_ignore = ignore.split(",") if ignore is not None else None
    split_select = select.split(",") if select is not None else None
    importance_threshold = Importance[threshold]
    show_progress_bar = progress
    split_modules = modules.split(",") if modules is not None else []

    split_levels = ["importance", "file_path"] if levels is None else levels.split(",")
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
