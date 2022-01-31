"""Cody Baker, Ben Dichter."""
import sys
import os
import numpy as np
from collections import OrderedDict
from typing import Union, Dict
from pathlib import Path

from . import importance_levels
from .register_checks import severity_levels  # For strictly internal use only

FilePathType = Union[Path, str]


def sort_by_descending_severity(check_results: list):
    """Order the dictionaries in the check_list by severity."""
    severities = [severity_levels[check_result["severity"]] for check_result in check_results]
    descending_indices = np.argsort(severities)[::-1]
    return [check_results[j] for j in descending_indices]


def organize_inspect_results(check_results: list):
    """Format the list of returned results from checks."""
    organized_results = OrderedDict({importance_level: list() for importance_level in importance_levels})
    for check_result in check_results:
        organized_results[check_result["importance"]].append(check_result)
    for importance_level, check_results in organized_results.items():
        if len(check_results) == 0:
            organized_results.pop(importance_level)
        else:
            organized_results[importance_level] = sort_by_descending_severity(check_results=check_results)
    return organized_results


def write_results(log_file_path: FilePathType, organized_results: Dict[str, list], overwrite=False):
    """Write the list of organized check results to a nicely formatted text file."""
    log_file_path = Path(log_file_path)

    if log_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {log_file_path} already exists! Set 'overwrite=True' or pass '-w True' flag.")

    nwbfile_index = 1  # TODO
    with open(file=log_file_path, mode="w", newline="\n") as file:
        nwbfile_name_string = "NWBFile: xxxxxx.nwb"  # TODO
        file.write(nwbfile_name_string + "\n")
        file.write("=" * len(nwbfile_name_string) + "\n")

        for importance_index, (importance_level, check_results) in enumerate(organized_results.items()):
            importance_string = importance_level.replace("_", " ")
            file.write(f"\n{importance_string}\n")
            file.write("-" * len(importance_level) + "\n")

            check_index = 1
            for check_result in check_results:
                file.write(
                    f"{nwbfile_index}.{importance_index}.{check_index}   {check_result['object_type']} "
                    f"'{check_result['object_name']}' located in '{check_result['location']}'\n"
                    f"        {check_result['check_function_name']}: {check_result['message']}\n"
                )
                check_index += 1


def print_to_console(log_file_path: FilePathType):
    """Print log file contents to console."""
    color_map = {
        "CRITICAL IMPORTANCE": "\x1b[31m",
        "BEST PRACTICE VIOLATION": "\x1b[33m",
        "BEST PRACTICE SUGGESTION": None,
    }
    reset_color = "\x1b[0m"

    with open(file=log_file_path, mode="r") as file:
        log_output = file.readlines()

    color_shift_points = dict()
    for line_index, line in enumerate(log_output):
        for color_trigger in color_map:
            if color_trigger in line:
                color_shift_points.update(
                    {line_index: color_map[color_trigger], line_index + 1: color_map[color_trigger]}
                )

    current_color = None
    for line_index, line in enumerate(log_output):
        transition_point = line_index in color_shift_points
        if transition_point:
            current_color = color_shift_points[line_index]
            log_output[line_index] = f"{current_color}{line}{reset_color}"
        if current_color is not None and not transition_point:
            log_output[line_index] = f"{current_color}{line[:6]}{reset_color}{line[6:]}"

    sys.stdout.write(os.linesep * 2)
    for line in log_output:
        sys.stdout.write(line)
