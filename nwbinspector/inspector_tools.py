"""Internally used tools specifically for rendering more human-readable output from collected check results."""
import sys
import os
from enum import Enum
from collections import OrderedDict
from typing import Dict, List
from pathlib import Path

import numpy as np

from .utils import FilePathType


class ReportCollectorImportance(Enum):
    """Additional importance levels applied to violations outside of NWBInspector."""

    ERROR = 4
    PYNWB_VALIDATION = 3
    CRITICAL = 2
    BEST_PRACTICE_VIOLATION = 1
    BEST_PRACTICE_SUGGESTION = 0


def sort_by_descending_severity(check_results: list):
    """Order the dictionaries in the check_list by severity."""
    severities = [check_result.severity.value for check_result in check_results]
    descending_indices = np.argsort(severities)[::-1]
    return [check_results[j] for j in descending_indices]


def organize_check_results(check_results: list):
    """Format the list of returned results from checks."""
    initial_results = OrderedDict({importance.name: list() for importance in ReportCollectorImportance})
    for check_result in check_results:
        initial_results[check_result.importance.name].append(check_result)
    organized_check_results = OrderedDict()
    for importance_level, check_results in initial_results.items():
        if any(check_results):
            organized_check_results.update({importance_level: sort_by_descending_severity(check_results=check_results)})
    return organized_check_results


def write_results(log_file_path: FilePathType, organized_results: Dict[str, Dict[str, list]], overwrite=False):
    """Write the list of organized check results to a nicely formatted text file."""
    log_file_path = Path(log_file_path)
    if log_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {log_file_path} already exists! Set 'overwrite=True' or pass '-o' flag.")
    num_nwbfiles = len(organized_results)
    with open(file=log_file_path, mode="w", newline="\n") as file:
        for nwbfile_index, (nwbfile_name, organized_check_results) in enumerate(organized_results.items(), start=1):
            nwbfile_name_string = f"NWBFile: {nwbfile_name}"
            file.write(nwbfile_name_string + "\n")
            file.write("=" * len(nwbfile_name_string) + "\n")

            for importance_index, (importance_level, check_results) in enumerate(
                organized_check_results.items(), start=1
            ):
                importance_string = importance_level.replace("_", " ")
                file.write(f"\n{importance_string}\n")
                file.write("-" * len(importance_level) + "\n")

                if importance_level in ["ERROR", "PYNWB_VALIDATION"]:
                    for check_index, check_result in enumerate(check_results, start=1):
                        file.write(
                            f"{nwbfile_index}.{importance_index}.{check_index}   {check_result.object_type} "
                            f"'{check_result.location}': {check_result.check_function_name}: {check_result.message}\n"
                        )
                else:
                    for check_index, check_result in enumerate(check_results, start=1):
                        file.write(
                            f"{nwbfile_index}.{importance_index}.{check_index}   {check_result.object_type} "
                            f"'{check_result.object_name}' located in '{check_result.location}'\n"
                            f"        {check_result.check_function_name}: {check_result.message}\n"
                        )
            if nwbfile_index != num_nwbfiles:
                file.write("\n\n\n")


def supports_color():  # pragma: no cover
    """
    Return True if the running system's terminal supports color, and False otherwise.

    From https://github.com/django/django/blob/main/django/core/management/color.py
    """

    def vt_codes_enabled_in_windows_registry():
        """Check the Windows Registry to see if VT code handling has been enabled by default."""
        try:
            # winreg is only available on Windows.
            import winreg
        except ImportError:
            return False
        else:
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Console")
            try:
                reg_key_value, _ = winreg.QueryValueEx(reg_key, "VirtualTerminalLevel")
            except FileNotFoundError:
                return False
            else:
                return reg_key_value == 1

    # isatty is not always implemented, #6223.
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

    return is_a_tty and (
        sys.platform != "win32"
        or "ANSICON" in os.environ
        or
        # Windows Terminal supports VT codes.
        "WT_SESSION" in os.environ
        or
        # Microsoft Visual Studio Code's built-in terminal supports colors.
        os.environ.get("TERM_PROGRAM") == "vscode"
        or vt_codes_enabled_in_windows_registry()
    )


def wrap_color(log_output: List[str], no_color: bool = False):  # pragma: no cover
    """Wrap the file output with colors for console output."""
    if not supports_color():
        no_color = True
    if not no_color:
        reset_color = "\x1b[0m"
        color_map = {
            "CRITICAL IMPORTANCE": "\x1b[31m",
            "BEST PRACTICE VIOLATION": "\x1b[33m",
            "BEST PRACTICE SUGGESTION": reset_color,
            "NWBFile": reset_color,
        }

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


def print_to_console(log_file_path: FilePathType, no_color: bool = False):
    """Print log file contents to console."""
    with open(file=log_file_path, mode="r") as file:
        log_output = file.readlines()
    wrap_color(log_output=log_output, no_color=no_color)
    sys.stdout.write(os.linesep * 2)
    for line in log_output:
        sys.stdout.write(line)
