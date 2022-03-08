"""Internally used tools specifically for rendering more human-readable output from collected check results."""
import os
import sys
from typing import Dict, List
from pathlib import Path
from natsort import natsorted
from enum import Enum

from .register_checks import Importance, InspectorMessage
from .utils import FilePathType


def fancy_organize_messages(messages: List[InspectorMessage], levels: List[str]):
    """General function for organizing list of InspectorMessages into a nested dictionary structure."""
    unique_values = list(set(getattr(message, levels[0]) for message in messages))
    sorted_values = sort_unique_values(unique_values)
    if len(levels) > 1:
        return {
            value: fancy_organize_messages(
                [message for message in messages if getattr(message, levels[0]) == value], levels[1:]
            )
            for value in sorted_values
        }
    else:
        return {
            value: [messages for message in messages if getattr(message, levels[0]) == value] for value in sorted_values
        }


def sort_unique_values(unique_values: set):
    """Technically, the 'set' method applies basic sorting to the unique contents, but natsort is more general."""
    if any(unique_values) and isinstance(unique_values[0], Enum):
        return natsorted(unique_values, key=lambda x: -x.value)
    else:
        return natsorted(unique_values)


def construct_output(presorted_level_values: list):
    """Construct an empty output dictionary according to the pre-sorted and unique levels."""
    if len(presorted_level_values) > 1:
        return {value: construct_output(presorted_level_values[1:]) for value in presorted_level_values[0]}
    else:
        return {value: list() for value in presorted_level_values[0]}


def append_output(output: dict, message: InspectorMessage, levels: list, loc=None):
    """Append message to list at final level of arbitrarily nested dictionary."""
    if loc is None:
        loc = output
    if len(levels) >= 1:
        loc = loc.get(getattr(message, levels[0]))
        return append_output(output=output, message=message, levels=levels[1:], loc=loc)
    else:
        loc.append(message)


def efficient_organize_messages(messages: List[InspectorMessage], levels: List[str]):
    """General function for organizing list of InspectorMessages into a nested dictionary structure."""
    presorted_level_values = list()
    for level in levels:
        presorted_level_values.append(
            sort_unique_values(unique_values=list(set(getattr(message, level) for message in messages)))
        )
    output = construct_output(presorted_level_values=presorted_level_values)

    for message in messages:
        append_output(output=output, message=message, levels=levels)
    return output


def organize_messages_by_file(messages: List[InspectorMessage]):
    """Order InspectorMessages by file name then importance."""
    files = natsorted(set(message.file for message in messages))
    importance_levels = [Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, Importance.BEST_PRACTICE_SUGGESTION]
    out = {file: {importance: list() for importance in importance_levels} for file in files}
    for message in messages:
        out[message.file][message.importance].append(message)
    for file in files:
        for importance in importance_levels:
            if out[file][importance]:
                out[file][importance] = sorted(out[file][importance], key=lambda x: -x.severity.value)
            else:
                out[file].pop(importance)
    return out


def organize_messages_by_importance(messages: List[InspectorMessage]):
    """Order InspectorMessages by importance, check function name, then file name."""
    out = dict()
    for message in natsorted(messages, key=lambda x: (-x.importance.value, -x.severity.value, x.file)):
        if message.importance not in out:
            out[message.importance] = dict()
        if message.check_function_name not in out[message.importance]:
            out[message.importance][message.check_function_name] = dict()
        if message.file not in out[message.importance][message.check_function_name]:
            out[message.importance][message.check_function_name][message.file] = []
        out[message.importance][message.check_function_name][message.file].append(message)
    return out


def display_messages_by_importance(messages: List[InspectorMessage], indent_size: int = 2):
    """Print InspectorMessages in order of importance."""
    indent = " " * indent_size
    disp = []
    data = organize_messages_by_importance(messages)
    for i, (importance, imp_data) in enumerate(data.items()):
        disp.append(f"{i}.  {importance.name}")
        disp.append("-" * (len(importance.name) + 4))
        for ii, (check_name, check_data) in enumerate(imp_data.items()):
            disp.append(f"{i}.{ii}.  {check_name}")
            counter = 0
            for file, file_messages in check_data.items():
                for message in file_messages:
                    disp.append(
                        f"{indent}{i}.{ii}.{counter}.  {file}:{message.location}{message.object_name} -"
                        f" {message.message}"
                    )
                    counter += 1
        disp.append("")
    return disp


def format_organized_results_output(organized_results: Dict[str, Dict[str, list]]) -> List[str]:
    """Convert organized_results structure into list of strings ready for console output or file write."""
    num_nwbfiles = len(organized_results)
    formatted_output = list()
    for nwbfile_index, (nwbfile_name, organized_check_results) in enumerate(organized_results.items(), start=1):
        nwbfile_name_string = f"NWBFile: {nwbfile_name}"
        formatted_output.append(nwbfile_name_string + "\n")
        formatted_output.append("=" * len(nwbfile_name_string) + "\n")

        for importance_index, (importance_level, check_results) in enumerate(organized_check_results.items(), start=1):
            importance_string = importance_level.name.replace("_", " ")
            formatted_output.append(f"\n{importance_string}\n")
            formatted_output.append("-" * len(importance_string) + "\n")

            if importance_level in ["ERROR", "PYNWB_VALIDATION"]:
                for check_index, check_result in enumerate(check_results, start=1):
                    formatted_output.append(
                        f"{nwbfile_index}.{importance_index}.{check_index}   {check_result.object_type} "
                        f"'{check_result.location}': {check_result.check_function_name}: {check_result.message}\n"
                    )
            else:
                for check_index, check_result in enumerate(check_results, start=1):
                    formatted_output.append(
                        f"{nwbfile_index}.{importance_index}.{check_index}   {check_result.object_type} "
                        f"'{check_result.object_name}' located in '{check_result.location}'\n"
                        f"        {check_result.check_function_name}: {check_result.message}\n"
                    )
        if nwbfile_index != num_nwbfiles:
            formatted_output.append("\n\n\n")
    return formatted_output


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
        or "WT_SESSION" in os.environ  # Windows Terminal supports VT codes.
        or os.environ.get("TERM_PROGRAM") == "vscode"  # Microsoft Visual Studio Code's built-in terminal.
        or vt_codes_enabled_in_windows_registry()
    )


def wrap_color(formatted_results: List[str], no_color: bool = False):  # pragma: no cover
    """Wrap the file output with colors for console output."""
    if not supports_color():
        return formatted_results
    reset_color = "\x1b[0m"
    color_map = {
        "CRITICAL IMPORTANCE": "\x1b[31m",
        "BEST PRACTICE VIOLATION": "\x1b[33m",
        "BEST PRACTICE SUGGESTION": reset_color,
        "NWBFile": reset_color,
    }

    color_shift_points = dict()
    for line_index, line in enumerate(formatted_results):
        for color_trigger in color_map:
            if color_trigger in line:
                color_shift_points.update(
                    {line_index: color_map[color_trigger], line_index + 1: color_map[color_trigger]}
                )
    colored_output = list()
    current_color = None
    for line in formatted_results:
        transition_point = line_index in color_shift_points
        if transition_point:
            current_color = color_shift_points[line_index]
            colored_output.append(f"{current_color}{line}{reset_color}")
        if current_color is not None and not transition_point:
            colored_output.append(f"{current_color}{line[:6]}{reset_color}{line[6:]}")


def print_to_console(formatted_results: List[str], no_color: bool = False):
    """Print log file contents to console."""
    wrap_color(formatted_results=formatted_results, no_color=no_color)
    sys.stdout.write(os.linesep * 2)
    for line in formatted_results:
        sys.stdout.write(line)


def save_report(report_file_path: FilePathType, formatted_results: List[str], overwrite=False):
    """Write the list of organized check results to a nicely formatted text file."""
    report_file_path = Path(report_file_path)
    if report_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {report_file_path} already exists! Set 'overwrite=True' or pass '-o' flag.")
    with open(file=report_file_path, mode="w", newline="\n") as file:
        for line in formatted_results:
            file.write(line)
