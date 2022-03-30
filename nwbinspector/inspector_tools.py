"""Internally used tools specifically for rendering more human-readable output from collected check results."""
import os
import sys
from typing import Dict, List, Optional, Union
from pathlib import Path
from natsort import natsorted
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from platform import platform
from importlib.metadata import version
from collections import defaultdict

import numpy as np

from .register_checks import InspectorMessage, Importance
from .utils import FilePathType


def _sort_unique_values(unique_values: list, reverse: bool = False):
    """Technically, the 'set' method applies basic sorting to the unique contents, but natsort is more general."""
    if any(unique_values) and isinstance(unique_values[0], Enum):
        return natsorted(unique_values, key=lambda x: -x.value, reverse=reverse)
    else:
        return natsorted(unique_values, reverse=reverse)


def organize_messages(messages: List[InspectorMessage], levels: List[str], reverse: Optional[List[bool]] = None):
    """
    General function for organizing list of InspectorMessages.

    Returns a nested dictionary organized according to the order of the 'levels' argument.

    Parameters
    ----------
    messages : list of InspectorMessages
    levels: list of strings
        Each string in this list must correspond onto an attribute of the InspectorMessage class, excluding the
        'message' text and 'object_name' (this will be coupled to the 'object_type').
    """
    assert all([x not in levels for x in ["message", "object_name", "severity"]]), (
        "You must specify levels to organize by that correspond to attributes of the InspectorMessage class, excluding "
        "the text message, object_name, and severity."
    )
    if reverse is None:
        reverse = [False] * len(levels)
    unique_values = list(set(getattr(message, levels[0]) for message in messages))
    sorted_values = _sort_unique_values(unique_values, reverse=reverse[0])
    if len(levels) > 1:
        return {
            value: organize_messages(
                messages=[message for message in messages if getattr(message, levels[0]) == value],
                levels=levels[1:],
                reverse=reverse[1:],
            )
            for value in sorted_values
        }
    else:
        return {
            value: sorted(
                [message for message in messages if getattr(message, levels[0]) == value],
                key=lambda x: -x.severity.value,
            )
            for value in sorted_values
        }


@dataclass
class FormatterOptions:
    """
    Class that defines all the format paramters used by the generic MessageFormatter.

    Parameters
    ----------
    indent_size : int, optional
        Defines the spacing between numerical sectioning and section name or message.
        Defaults to 2 spaces.
    """

    indent_size: int = 2
    indent: str = " " * indent_size
    # TODO
    # Future custom options could include section break sizes, control over header characters, section-specific indents


class MessageFormatter:
    """For full customization of all format paramters, use this class instead of the 'format_messages' function."""

    def __init__(
        self,
        messages: List[InspectorMessage],
        levels: List[str],
        reverse: Optional[List[bool]] = None,
        detailed: bool = False,
        formatter_options: Optional[FormatterOptions] = None,
    ):
        self.nmessages = len(messages)
        self.nfiles = len(set(message.file_path for message in messages))
        self.message_count_by_importance = self._count_messages_by_importance(messages=messages)
        self.initial_organized_messages = organize_messages(messages=messages, levels=levels)
        self.detailed = detailed
        self.levels = levels
        self.nlevels = len(levels)
        self.free_levels = (
            set([x for x in InspectorMessage.__annotations__])
            - set(levels)
            - set(["message", "object_name", "severity"])
        )
        self.collection_levels = set([x for x in InspectorMessage.__annotations__]) - set(levels) - set(["severity"])
        self.reverse = reverse
        if formatter_options is None:
            self.formatter_options = FormatterOptions()
        else:
            assert isinstance(
                formatter_options, FormatterOptions
            ), "'formatter_options' is not an instance of FormatterOptions!"
            self.formatter_options = formatter_options
        self.message_counter = 0
        self.formatted_messages = []

    def _count_messages_by_importance(self, messages: List[InspectorMessage]) -> Dict[str, int]:
        message_count_by_importance = {importance_level.name: 0 for importance_level in Importance}
        for message in messages:
            message_count_by_importance[message.importance.name] += 1
        for key in [keys for keys, count in message_count_by_importance.items() if count == 0]:
            message_count_by_importance.pop(key)
        return message_count_by_importance

    def _get_name(self, obj) -> str:
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, str):
            return obj

    def _add_subsection(
        self,
        organized_messages: Dict[str, Union[dict, List[InspectorMessage]]],
        levels: List[str],
        level_counter: List[int],
    ):
        """Recursive helper for display_messages."""
        this_level_counter = list(level_counter)  # local copy passed from previous recursion level
        if len(levels) > 1:
            this_level_counter.append(0)
            for i, (key, val) in enumerate(organized_messages.items()):  # Add section header and recurse
                this_level_counter[-1] = i
                increment = f"{'.'.join(np.array(this_level_counter, dtype=str))}{self.formatter_options.indent}"
                section_name = f"{increment}{self._get_name(obj=key)}"
                self.formatted_messages.append(section_name)
                self.formatted_messages.extend(["-" * len(section_name), ""])
                self._add_subsection(organized_messages=val, levels=levels[1:], level_counter=this_level_counter)
        else:  # Final section, display message information
            if levels[0] == "file_path" and not self.detailed:
                # Collect messages into unique parts based on available submessage information in the
                # 'free_levels' plus 'message' and 'object_name'
                submessages = [
                    tuple([getattr(message, attr) for attr in self.collection_levels])
                    for file_path, messages in organized_messages.items()
                    for message in messages
                ]
                unique_submessages = set(submessages)
                unique_counter = defaultdict(int)
                for submessage in submessages:
                    unique_counter[submessage] += 1
                first_file_path = dict()
                for unique_submessage in unique_submessages:
                    first_file_path[unique_submessage] = next(
                        (file_path for (file_path, message), submessage in zip(organized_messages.items(), submessages))
                    )
            # Display only the unique messages and first 'file_path' + counter for each
            # TODO
            else:
                for key, val in organized_messages.items():
                    for message in val:
                        message_header = ""
                        if "file_path" in self.free_levels:
                            message_header += f"{message.file_path} - "
                        if "check_function_name" in self.free_levels:
                            message_header += f"{message.check_function_name} - "
                        if "importance" in self.free_levels:
                            message_header += f"Importance level '{message.importance.name}' "
                        if "object_type" in self.free_levels:
                            message_header += f"'{message.object_type}' "
                        if "object_name" in self.free_levels:
                            message_header += f"object '{message.object_name}' "
                        if "location" in self.free_levels and message.location not in ["", "/"]:
                            message_header += f"located in '{message.location}' "
                        increment = (
                            f"{'.'.join(np.array(this_level_counter, dtype=str))}.{self.message_counter}"
                            f"{self.formatter_options.indent}"
                        )
                        self.formatted_messages.append(f"{increment}{key}: {message_header.rstrip(' - ')}")
                        self.formatted_messages.extend([f"{' ' * len(increment)}  Message: {message.message}", ""])
                        self.message_counter += 1

    def format_messages(self) -> List[str]:
        """Deploy recursive addition of sections, termining with message display."""
        self.formatted_messages.extend(
            [
                "*" * 50,
                "NWBInspector Report Summary",
                "",
                f"Timestamp: {str(datetime.now().astimezone())}",
                f"Platform: {platform()}",
                f"NWBInspector version: {version('nwbinspector')}",
                "",
                f"Found {self.nmessages} issues over {self.nfiles} files:",
            ]
        )
        for importance_level, number_of_results in self.message_count_by_importance.items():
            increment = " " * (8 - len(str(number_of_results)))
            self.formatted_messages.append(f"{increment}{number_of_results} - {importance_level}")
        self.formatted_messages.extend(["*" * 50, "", ""])
        self._add_subsection(organized_messages=self.initial_organized_messages, levels=self.levels, level_counter=[])
        return self.formatted_messages


def format_messages(
    messages: List[InspectorMessage], levels: List[str], reverse: Optional[List[bool]] = None
) -> List[str]:
    """Print InspectorMessages in order specified by the organization structure."""
    message_formatter = MessageFormatter(messages=messages, levels=levels, reverse=reverse)
    formatted_messages = message_formatter.format_messages()
    return formatted_messages


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


def wrap_color(formatted_messages: List[str], no_color: bool = False):  # pragma: no cover
    """Wrap the file output with colors for console output."""
    if not supports_color():
        return formatted_messages
    reset_color = "\x1b[0m"
    color_map = {
        "CRITICAL IMPORTANCE": "\x1b[31m",
        "BEST PRACTICE VIOLATION": "\x1b[33m",
        "BEST PRACTICE SUGGESTION": reset_color,
        "NWBFile": reset_color,
    }

    color_shift_points = dict()
    for line_index, line in enumerate(formatted_messages):
        for color_trigger in color_map:
            if color_trigger in line:
                color_shift_points.update(
                    {line_index: color_map[color_trigger], line_index + 1: color_map[color_trigger]}
                )
    colored_output = list()
    current_color = None
    for line in formatted_messages:
        transition_point = line_index in color_shift_points
        if transition_point:
            current_color = color_shift_points[line_index]
            colored_output.append(f"{current_color}{line}{reset_color}")
        if current_color is not None and not transition_point:
            colored_output.append(f"{current_color}{line[:6]}{reset_color}{line[6:]}")


def print_to_console(formatted_messages: List[str], no_color: bool = False):
    """Print report file contents to console."""
    wrap_color(formatted_messages=formatted_messages, no_color=no_color)
    sys.stdout.write(os.linesep * 2)
    for line in formatted_messages:
        sys.stdout.write(line + "\n")


def save_report(report_file_path: FilePathType, formatted_messages: List[str], overwrite=False):
    """Write the list of organized check results to a nicely formatted text file."""
    report_file_path = Path(report_file_path)
    if report_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {report_file_path} already exists! Set 'overwrite=True' or pass '-o' flag.")
    with open(file=report_file_path, mode="w", newline="\n") as file:
        for line in formatted_messages:
            file.write(line + "\n")
