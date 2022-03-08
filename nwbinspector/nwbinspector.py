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


class InspectorOutputJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for the NWBInspector."""

    def default(self, o):
        if isinstance(o, InspectorMessage):
            return o.__dict__
        if isinstance(o, Enum):
            return o.name
        else:
            return super().default(o)


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
@click.option("-s", "--select", help="Comma-separated names of checks to run")
@click.option(
    "-t",
    "--threshold",
    default="BEST_PRACTICE_SUGGESTION",
    type=click.Choice(["CRITICAL", "BEST_PRACTICE_VIOLATION", "BEST_PRACTICE_SUGGESTION"]),
    help="Ignores tests with an assigned importance below this threshold.",
)
@click.option("-c", "--config-path", help="path of config .yaml file that overwrites importance of checks.")
@click.option("-j", "--json-file-path", help="Write json output to this location.")
def inspect_all_cli(
    path: str,
    modules: Optional[str] = None,
    no_color: bool = False,
    report_file_path: str = None,
    overwrite: bool = False,
    ignore: Optional[str] = None,
    select: Optional[str] = None,
    threshold: str = "BEST_PRACTICE_SUGGESTION",
    config_path: Optional[str] = None,
    json_file_path: str = None,
):
    """Primary CLI usage."""
    if config_path is not None:
        with open(file=config_path, mode="r") as stream:
            config = yaml.load(stream, yaml.Loader)
        with open(file=Path(__file__).parent / "config.schema.json", mode="r") as fp:
            schema = json.load(fp=fp)
        jsonschema.validate(config, schema)
    else:
        config = None
    messages = inspect_all(
        path,
        modules=modules,
        config=config,
        ignore=ignore if ignore is None else ignore.split(","),
        select=select if select is None else select.split(","),
        importance_threshold=Importance[threshold],
    )
    if json_file_path is not None:
        with open(json_file_path, "w") as fp:
            json.dump(messages, fp, cls=InspectorOutputJSONEncoder)
    if len(messages):
        organized_results = organize_messages_by_file(messages=messages)
        formatted_results = format_organized_results_output(organized_results=organized_results)
        print_to_console(formatted_results=formatted_results, no_color=no_color)
        if report_file_path is not None:
            save_report(report_file_path=report_file_path, formatted_results=formatted_results, overwrite=overwrite)
            print(f"{os.linesep*2}Log file saved at {str(report_file_path.absolute())}!{os.linesep}")


def inspect_all(
    path: PathType,
    modules: OptionalListOfStrings = None,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
    config: dict = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
):
    """Inspect all NWBFiles at the specified path."""
    modules = modules or []
    path = Path(path)

    in_path = Path(path)
    if in_path.is_dir():
        nwbfiles = list(in_path.glob("*.nwb"))
    elif in_path.is_file():
        nwbfiles = [in_path]
    else:
        raise ValueError(f"{in_path} should be a directory or an NWB file.")
    if config is not None:
        checks = configure_checks(config, available_checks)
    else:
        checks = available_checks
    for module in modules:
        importlib.import_module(module)
    messages = list()
    for nwbfile_path in nwbfiles:
        messages.extend(
            inspect_nwb(
                nwbfile_path=nwbfile_path,
                checks=checks,
                importance_threshold=importance_threshold,
                ignore=ignore,
                select=select,
            )
        )
    return messages


def configure_checks(config: dict, checks: list = available_checks) -> list:
    """Filter a list of check functions (the entire base registry by default) according to the configuration."""
    checks_out = []
    for check in checks:
        for importance_name, func_names in config.items():
            if check.__name__ in func_names:
                if importance_name == "SKIP":
                    continue
                check.importance = Importance[importance_name]
        checks_out.append(check)
    return checks_out


def inspect_nwb(
    nwbfile_path: FilePathType,
    checks: list = available_checks,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
    ignore: OptionalListOfStrings = None,
    select: OptionalListOfStrings = None,
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
    driver: str, optional
        Forwarded to h5py.File(). Set to "ros3" for reading from s3 url.
    """
    if ignore is not None and select is not None:
        raise ValueError("Options 'ignore' and 'select' cannot both be used.")
    if importance_threshold not in Importance:
        raise ValueError(
            f"Indicated importance_threshold ({importance_threshold}) is not a valid importance level! Please choose "
            "from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION]."
        )
    file_name = Path(nwbfile_path).name
    messages = list()
    try:
        with pynwb.NWBHDF5IO(path=str(nwbfile_path), mode="r", load_namespaces=True, driver=driver) as io:
            validation_errors = pynwb.validate(io=io)
            if any(validation_errors):
                for validation_error in validation_errors:
                    message = InspectorMessage(message=validation_error.reason)
                    message.importance = Importance.PYNWB_VALIDATION
                    message.check_function_name = validation_error.name
                    message.location = validation_error.location
                    message.file = file_name
                    messages.append(message)
            nwbfile = io.read()
            for check_function in checks:
                if (
                    (ignore is not None and check_function.__name__ in ignore)
                    or (select is not None and check_function.__name__ not in select)
                    or (check_function.importance.value < importance_threshold.value)
                ):
                    continue
                for nwbfile_object in nwbfile.objects.values():
                    if issubclass(type(nwbfile_object), check_function.neurodata_type):
                        message = check_function(nwbfile_object)
                        if message is not None:
                            message.file = file_name
                            if isinstance(message, Iterable):
                                messages.extend(message)
                            else:
                                messages.append(message)
    except Exception as ex:
        message = InspectorMessage(message=traceback.format_exc())
        message.importance = Importance.ERROR
        message.check_function_name = f"{type(ex)}: {str(ex)}"
        message.file = file_name
        messages.append(message)
    return messages


if __name__ == "__main__":
    inspect_all_cli()
