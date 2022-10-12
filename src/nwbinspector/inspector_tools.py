"""Internally used tools specifically for rendering more human-readable output from collected check results."""
import os
import sys
from typing import Dict, List, Optional, Union
from pathlib import Path
from enum import Enum
from datetime import datetime
from platform import platform
from collections import defaultdict

from natsort import natsorted

import numpy as np

from .register_checks import InspectorMessage, Importance
from .utils import FilePathType, get_package_version


def get_report_header():
    """Grab basic information from system at time of report generation."""
    return dict(
        Timestamp=str(datetime.now().astimezone()),
        Platform=platform(),
        NWBInspector_version=get_package_version("nwbinspector"),
    )


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


class FormatterOptions:
    """Class structure for defining all free attributes for the design of a report format."""

    def __init__(
        self, indent_size: int = 2, indent: Optional[str] = None, section_headers: List[str] = ["=", "-", "~"]
    ):
        """
        Class that defines all the format parameters used by the generic MessageFormatter.

        Parameters
        ----------
        indent_size : int, optional
            Defines the spacing between numerical sectioning and section name or message.
            Defaults to 2 spaces.
        indent : str, optional
            Defines the specific indentation to inject between numerical sectioning and section name or message.
            Overrides indent_size.
            Defaults to " " * indent_size.
        section_headers : list of strings, optional
            List of characters that will be injected under the display of each new section of the report.
            If levels is longer than this list, the last item will be repeated over the remaining levels.
            If levels is shorter than this list, only the first len(levels) of items will be used.
            Defaults to the .rst style for three sub-sections: ["=", "-", "~"]
        """
        # TODO
        # Future custom options could include section break sizes, section-specific indents, etc.
        self.indent = indent if indent is not None else " " * indent_size
        self.section_headers = section_headers


class MessageFormatter:
    """For full customization of all format parameters, use this class instead of the 'format_messages' function."""

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
        self.initial_organized_messages = organize_messages(messages=messages, levels=levels, reverse=reverse)
        self.detailed = detailed
        self.levels = levels
        self.nlevels = len(levels)
        self.free_levels = (
            set([x for x in InspectorMessage.__annotations__]) - set(levels) - set(["message", "severity"])
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
        self.formatter_options.section_headers.extend(
            [self.formatter_options.section_headers[-1]] * (self.nlevels - len(self.formatter_options.section_headers))
        )
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

    def _get_message_header(self, message: InspectorMessage):
        message_header = ""
        if "file_path" in self.free_levels:
            message_header += f"{message.file_path} - "
        if "check_function_name" in self.free_levels:
            message_header += f"{message.check_function_name} - "
        if "importance" in self.free_levels:
            message_header += f"Importance level '{message.importance.name}' - "
        if any((x in self.free_levels for x in ["object_type", "object_name"])):
            message_header += f"'{message.object_type}' object "
        if "location" in self.free_levels and message.location:
            message_header += f"at location '{message.location}'"
        else:
            message_header += f"with name '{message.object_name}'"
        return message_header

    def _get_message_increment(self, level_counter: List[int]):
        return (
            f"{'.'.join(np.array(level_counter, dtype=str))}.{self.message_counter}" f"{self.formatter_options.indent}"
        )

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
                self.formatted_messages.extend(
                    [f"{self.formatter_options.section_headers[len(this_level_counter) - 1]}" * len(section_name), ""]
                )
                self._add_subsection(organized_messages=val, levels=levels[1:], level_counter=this_level_counter)
        else:  # Final section, display message information
            if levels[0] == "file_path" and not self.detailed:
                # Collect messages into unique parts based on available submessage information in the
                # 'free_levels' plus 'message' and 'object_name'
                binned_messages = defaultdict(list)
                for file_path, messages in organized_messages.items():
                    for message in messages:
                        submessage = tuple([getattr(message, attr) for attr in self.collection_levels])
                        binned_messages[submessage].append(message)
                # Display only the unique messages and first 'file_path' + counter for each
                for same_messages in binned_messages.values():
                    message = same_messages[0]
                    increment = self._get_message_increment(level_counter=this_level_counter)
                    message_header = self._get_message_header(message=message)
                    num_same = len(same_messages)
                    file_or_files = "s" if num_same > 2 else ""
                    additional_file_str = f" and {num_same-1} other file{file_or_files}" if num_same > 1 else ""
                    self.formatted_messages.append(
                        f"{increment}{message.file_path}{additional_file_str}: " f"{message_header.rstrip(' - ')}"
                    )
                    self.formatted_messages.extend([f"{' ' * len(increment)}  Message: {message.message}", ""])
                    self.message_counter += 1
            else:
                for key, val in organized_messages.items():
                    for message in val:
                        increment = self._get_message_increment(level_counter=this_level_counter)
                        message_header = self._get_message_header(message=message)
                        self.formatted_messages.append(f"{increment}{key}: {message_header.rstrip(' - ')}")
                        self.formatted_messages.extend([f"{' ' * len(increment)}  Message: {message.message}", ""])
                        self.message_counter += 1

    def format_messages(self) -> List[str]:
        """Deploy recursive addition of sections, terminating with message display."""
        report_header = get_report_header()
        self.formatted_messages.extend(
            [
                "*" * 50,
                "NWBInspector Report Summary",
                "",
                f"Timestamp: {report_header['Timestamp']}",
                f"Platform: {report_header['Platform']}",
                f"NWBInspector version: {report_header['NWBInspector_version']}",
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
    messages: List[InspectorMessage],
    levels: List[str] = None,
    reverse: Optional[List[bool]] = None,
    detailed: bool = False,
) -> List[str]:
    """Print InspectorMessages in order specified by the organization structure."""
    if levels is None:
        levels = ["file_path", "importance"]
    message_formatter = MessageFormatter(messages=messages, levels=levels, reverse=reverse, detailed=detailed)
    formatted_messages = message_formatter.format_messages()
    return formatted_messages


def print_to_console(formatted_messages: List[str]):
    """Print report file contents to console."""
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
