"""Internally used tools specifically for rendering more human-readable output from collected check results."""

import json
import os
import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from platform import platform
from typing import Any, Optional, Union

import numpy as np
from packaging.version import Version

from ._organization import organize_messages
from ._types import Importance, InspectorMessage
from .utils import get_package_version


class InspectorOutputJSONEncoder(json.JSONEncoder):
    """Custom JSONEncoder for the NWBInspector."""

    def default(self, o: object) -> Any:  # noqa D102
        if isinstance(o, InspectorMessage):
            return o.__dict__
        if isinstance(o, Enum):
            return o.name
        if isinstance(o, Version):
            return str(o)
        else:
            return super().default(o)


def _get_report_header() -> dict[str, str]:
    """Grab basic information from system at time of report generation."""
    return dict(
        Timestamp=str(datetime.now().astimezone()),
        Platform=platform(),
        NWBInspector_version=get_package_version("nwbinspector"),
    )


class MessageFormatter(ABC):
    """
    Abstract base class for message formatters.

    For full customization of all format parameters, subclass this class and implement
    the abstract methods.
    """

    # Section header characters to use for each level of nesting
    section_headers: tuple[str, ...] = ("=", "-", "~")
    # Indentation between numerical sectioning and section name or message
    indent: str = "  "

    def __init__(
        self,
        messages: list[Optional[InspectorMessage]],
        levels: list[str],
        reverse: Optional[list[bool]] = None,
        detailed: bool = False,
        nfiles_detected: Optional[int] = None,
    ) -> None:
        self.nmessages = len(messages)
        self.nfiles_with_issues = len(set(message.file_path for message in messages))  # type: ignore
        self.nfiles_detected = nfiles_detected
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
        # Extend section_headers to cover all levels
        self._extended_section_headers = self.section_headers + (self.section_headers[-1],) * (
            self.nlevels - len(self.section_headers)
        )
        self.message_counter = 0
        self.formatted_messages: list = []

    @staticmethod
    def _count_messages_by_importance(messages: list[Optional[InspectorMessage]]) -> dict[str, int]:
        message_count_by_importance = {importance_level.name: 0 for importance_level in Importance}
        for message in messages:
            message_count_by_importance[message.importance.name] += 1  # type: ignore
        for key in [keys for keys, count in message_count_by_importance.items() if count == 0]:
            message_count_by_importance.pop(key)
        return message_count_by_importance

    @staticmethod
    def _get_name(obj: Union[Enum, str]) -> str:
        if isinstance(obj, Enum):
            return obj.name
        if isinstance(obj, str):
            return obj

    def _get_message_header(self, message: InspectorMessage) -> str:
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

    def _get_message_increment(self, level_counter: list[int]) -> str:
        return f"{'.'.join(np.array(level_counter, dtype=str))}.{self.message_counter}{self.indent}"

    @abstractmethod
    def _format_section_header(self, section_name: str, level: int) -> list[str]:
        """
        Format a section header for the specific output format.

        Parameters
        ----------
        section_name : str
            The name/title of the section including the numerical prefix.
        level : int
            The nesting level of the section (0-indexed).

        Returns
        -------
        list of str
            The formatted section header lines to append to the output.
        """
        pass

    def _get_report_prefix(self) -> list[str]:
        """Return lines to add at the very start of the report. Override for formats like HTML."""
        return []

    def _get_report_suffix(self) -> list[str]:
        """Return lines to add at the very end of the report. Override for formats like HTML."""
        return []

    def _format_report_summary(self, report_header: dict[str, str]) -> list[str]:
        """Format the report summary section. Override for format-specific styling."""
        lines = [
            "*" * 50,
            "NWBInspector Report Summary",
            "",
            f"Timestamp: {report_header['Timestamp']}",
            f"Platform: {report_header['Platform']}",
            f"NWBInspector version: {report_header['NWBInspector_version']}",
            "",
        ]

        if self.nfiles_detected is not None:
            lines.append(f"Scanned {self.nfiles_detected} file(s).")
        if self.nmessages == 0:
            lines.append("No issues found!")
        else:
            lines.append(f"Found {self.nmessages} issues across {self.nfiles_with_issues} file(s):")

        for importance_level, number_of_results in self.message_count_by_importance.items():
            increment = " " * (8 - len(str(number_of_results)))
            lines.append(f"{increment}{number_of_results} - {importance_level}")

        lines.extend(["*" * 50, "", ""])
        return lines

    def _add_subsection(
        self,
        organized_messages: dict,
        levels: list[str],
        level_counter: list[int],
    ) -> None:
        """Recursive helper for display_messages."""
        this_level_counter = list(level_counter)  # local copy passed from previous recursion level
        if len(levels) > 1:
            this_level_counter.append(0)
            for i, (key, val) in enumerate(organized_messages.items()):  # Add section header and recurse
                this_level_counter[-1] = i
                increment = f"{'.'.join(np.array(this_level_counter, dtype=str))}{self.indent}"
                section_name = f"{increment}{self._get_name(obj=key)}"
                level = len(this_level_counter) - 1
                self.formatted_messages.extend(self._format_section_header(section_name=section_name, level=level))
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

    def format_messages(self) -> list[str]:
        """Deploy recursive addition of sections, terminating with message display."""
        # Add format-specific prefix (e.g., HTML doctype and opening tags)
        self.formatted_messages.extend(self._get_report_prefix())

        # Add format-specific report summary
        report_header = _get_report_header()
        self.formatted_messages.extend(self._format_report_summary(report_header))

        # Add the organized messages
        self._add_subsection(organized_messages=self.initial_organized_messages, levels=self.levels, level_counter=[])

        # Add format-specific suffix (e.g., HTML closing tags)
        self.formatted_messages.extend(self._get_report_suffix())

        return self.formatted_messages


class RstFormatter(MessageFormatter):
    """Formatter that outputs in reStructuredText (RST) format with underline-style section headers."""

    section_headers: tuple[str, ...] = ("=", "-", "~")

    def _format_section_header(self, section_name: str, level: int) -> list[str]:
        """Format section header using RST underline style."""
        header_char = self._extended_section_headers[level]
        return [section_name, header_char * len(section_name), ""]


class MarkdownFormatter(MessageFormatter):
    """Formatter that outputs in Markdown format with prefix-style section headers (#, ##, ###)."""

    section_headers: tuple[str, ...] = ("#", "##", "###")

    def _format_section_header(self, section_name: str, level: int) -> list[str]:
        """Format section header using Markdown prefix style."""
        header_prefix = self._extended_section_headers[level]
        return [f"{header_prefix} {section_name}", ""]


class HtmlFormatter(MessageFormatter):
    """Formatter that outputs in HTML format with proper document structure."""

    section_headers: tuple[str, ...] = ("h2", "h3", "h4", "h5", "h6")

    def _get_report_prefix(self) -> list[str]:
        """Return HTML document opening structure."""
        return [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "    <meta charset='utf-8'>",
            "    <title>NWBInspector Report</title>",
            "    <style>",
            "        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 40px; background: #f8f9fa; }",
            "        .summary { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }",
            "        .summary h1 { margin-top: 0; color: #333; }",
            "        .summary-meta { color: #666; font-size: 14px; margin-bottom: 20px; }",
            "        .summary-stats { background: #f8f9fa; padding: 15px; border-radius: 4px; }",
            "        .importance-list { list-style: none; padding: 0; margin: 10px 0 0 0; }",
            "        .importance-list li { padding: 5px 0; }",
            "        .importance-count { font-weight: bold; color: #333; }",
            "        .critical { color: #dc3545; }",
            "        .best-practice-violation { color: #fd7e14; }",
            "        .best-practice-suggestion { color: #ffc107; }",
            "        h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-top: 30px; }",
            "        h3 { color: #555; margin-top: 20px; }",
            "        .message { margin: 15px 0; padding: 15px; background: #fff; border-left: 4px solid #007bff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }",
            "        .message-header { font-weight: 500; color: #333; }",
            "        .message-content { color: #666; margin-top: 8px; }",
            "    </style>",
            "</head>",
            "<body>",
        ]

    def _get_report_suffix(self) -> list[str]:
        """Return HTML document closing structure."""
        return [
            "</body>",
            "</html>",
        ]

    def _format_report_summary(self, report_header: dict[str, str]) -> list[str]:
        """Format the report summary section with HTML styling."""
        lines = [
            "<div class='summary'>",
            "    <h1>NWBInspector Report</h1>",
            "    <div class='summary-meta'>",
            f"        <p><strong>Timestamp:</strong> {report_header['Timestamp']}</p>",
            f"        <p><strong>Platform:</strong> {report_header['Platform']}</p>",
            f"        <p><strong>NWBInspector version:</strong> {report_header['NWBInspector_version']}</p>",
            "    </div>",
            "    <div class='summary-stats'>",
        ]

        if self.nfiles_detected is not None:
            lines.append(f"        <p>Scanned <strong>{self.nfiles_detected}</strong> file(s).</p>")

        if self.nmessages == 0:
            lines.append("        <p style='color: #28a745; font-weight: bold;'>✓ No issues found!</p>")
        else:
            lines.append(
                f"        <p>Found <strong>{self.nmessages}</strong> issues across <strong>{self.nfiles_with_issues}</strong> file(s):</p>"
            )
            lines.append("        <ul class='importance-list'>")
            for importance_level, number_of_results in self.message_count_by_importance.items():
                css_class = importance_level.lower().replace("_", "-")
                lines.append(
                    f"            <li><span class='importance-count {css_class}'>{number_of_results}</span> {importance_level}</li>"
                )
            lines.append("        </ul>")

        lines.extend(
            [
                "    </div>",
                "</div>",
                "",
            ]
        )
        return lines

    def _format_section_header(self, section_name: str, level: int) -> list[str]:
        """Format section header using HTML heading tags."""
        tag = self._extended_section_headers[min(level, len(self._extended_section_headers) - 1)]
        return [f"<{tag}>{section_name}</{tag}>", ""]


def format_messages(
    messages: list[Optional[InspectorMessage]],
    levels: Optional[list[str]] = None,
    reverse: Optional[list[bool]] = None,
    detailed: bool = False,
    nfiles_detected: Optional[int] = None,
    output_format: str = "rst",
) -> list[str]:
    """Print InspectorMessages in order specified by the organization structure.

    Parameters
    ----------
    messages : list of InspectorMessage
        The messages to format.
    levels : list of str, optional
        The levels to organize by. Defaults to ["file_path", "importance"].
    reverse : list of bool, optional
        Whether to reverse each level. Defaults to False for all levels.
    detailed : bool, optional
        Whether to show detailed output. Defaults to False.
    nfiles_detected : int, optional
        Number of files detected during inspection.
    output_format : str, optional
        The output format for the report. Can be "rst" or "markdown".
        Defaults to "rst".

    Returns
    -------
    list of str
        The formatted message lines.
    """
    levels = levels or ["file_path", "importance"]

    # Select the appropriate formatter class based on output format
    formatter_class: type[MessageFormatter]
    if output_format == "markdown":
        formatter_class = MarkdownFormatter
    elif output_format == "html":
        formatter_class = HtmlFormatter
    else:
        formatter_class = RstFormatter

    message_formatter = formatter_class(
        messages=messages,
        levels=levels,
        reverse=reverse,
        detailed=detailed,
        nfiles_detected=nfiles_detected,
    )
    formatted_messages = message_formatter.format_messages()

    return formatted_messages


def print_to_console(formatted_messages: list[str]) -> None:
    """Print report file contents to console."""
    sys.stdout.write(os.linesep * 2)
    for line in formatted_messages:
        sys.stdout.write(line + "\n")

    return None


def save_report(report_file_path: Union[str, Path], formatted_messages: list[str], overwrite: bool = False) -> None:
    """Write the list of organized check results to a nicely formatted text file."""
    report_file_path = Path(report_file_path)

    if report_file_path.exists() and not overwrite:
        raise FileExistsError(f"The file {report_file_path} already exists! Set 'overwrite=True' or pass '-o' flag.")

    with open(file=report_file_path, mode="w", newline="\n") as file:
        for line in formatted_messages:
            file.write(line + "\n")

    return None
