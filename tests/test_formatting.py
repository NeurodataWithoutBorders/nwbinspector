"""Tests for the _formatting module."""

from unittest import TestCase

from nwbinspector import Importance, InspectorMessage
from nwbinspector._formatting import MessageFormatter


class TestMessageFormatterSummary(TestCase):
    """Test the summary message generation in MessageFormatter.format_messages()."""

    def test_format_messages_no_issues(self):
        """Test that the correct summary is generated when no issues are found."""
        messages = []
        levels = ["file_path", "importance"]
        nfiles_detected = 5

        formatter = MessageFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()
        self.assertIn("Scanned 5 file(s).", formatted_messages)
        self.assertIn("No issues found!", formatted_messages)

    def test_format_messages_with_issues(self):
        """Test that the correct summary is generated when issues are found."""
        messages = [
            InspectorMessage(
                message="Test issue 1",
                importance=Importance.CRITICAL,
                check_function_name="test_check",
                object_type="TestType",
                object_name="test_object",
                location="/test/location",
                file_path="/path/to/file1.nwb",
            ),
            InspectorMessage(
                message="Test issue 1",
                importance=Importance.CRITICAL,
                check_function_name="test_check",
                object_type="TestType",
                object_name="test_object",
                location="/test/location",
                file_path="/path/to/file1.nwb",
            ),
            InspectorMessage(
                message="Test issue 2",
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="test_check_2",
                object_type="TestType",
                object_name="test_object_2",
                location="/test/location2",
                file_path="/path/to/file2.nwb",
            ),
        ]
        levels = ["file_path", "importance"]
        nfiles_detected = 4

        formatter = MessageFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()

        self.assertIn("Scanned 4 file(s).", formatted_messages)
        self.assertIn("Found 3 issues across 2 file(s):", formatted_messages)
