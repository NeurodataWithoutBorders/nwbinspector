"""Tests for the _formatting module."""

from unittest import TestCase
from unittest.mock import patch

from nwbinspector import Importance, InspectorMessage
from nwbinspector._formatting import RstFormatter, MarkdownFormatter, HtmlFormatter


class TestMessageFormatterSummary(TestCase):
    """Test the summary message generation in MessageFormatter.format_messages()."""

    @patch("nwbinspector._formatting._get_report_header")
    def test_format_messages_no_issues(self, mock_header):
        """Test that the correct summary is generated when no issues are found."""
        mock_header.return_value = {
            "Timestamp": "2024-01-01 00:00:00",
            "Platform": "TestPlatform",
            "NWBInspector_version": "0.0.0",
        }
        messages = []
        levels = ["file_path", "importance"]
        nfiles_detected = 5

        formatter = RstFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()
        self.assertIn("Scanned 5 file(s).", formatted_messages)
        self.assertIn("No issues found!", formatted_messages)

    @patch("nwbinspector._formatting._get_report_header")
    def test_format_messages_with_issues(self, mock_header):
        """Test that the correct summary is generated when issues are found."""
        mock_header.return_value = {
            "Timestamp": "2024-01-01 00:00:00",
            "Platform": "TestPlatform",
            "NWBInspector_version": "0.0.0",
        }
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

        formatter = RstFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()

        self.assertIn("Scanned 4 file(s).", formatted_messages)
        self.assertIn("Found 3 issues across 2 file(s):", formatted_messages)


class TestFormatterCompleteOutput(TestCase):
    """Test the complete output string for each formatter."""

    def _create_test_message(self):
        """Create a single test message for consistent testing."""
        return InspectorMessage(
            message="Test message",
            importance=Importance.CRITICAL,
            check_function_name="test_check",
            object_type="TestType",
            object_name="test_object",
            location="/test/location",
            file_path="/path/to/file.nwb",
        )

    @patch("nwbinspector._formatting._get_report_header")
    def test_rst_formatter_complete_output(self, mock_header):
        """Test that RstFormatter produces the exact expected RST output."""
        mock_header.return_value = {
            "Timestamp": "2024-01-01 00:00:00",
            "Platform": "TestPlatform",
            "NWBInspector_version": "0.0.0",
        }
        messages = [self._create_test_message()]
        levels = ["importance", "file_path"]
        nfiles_detected = 1

        formatter = RstFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()
        output = "\n".join(formatted_messages)

        expected_output = """**************************************************
NWBInspector Report Summary

Timestamp: 2024-01-01 00:00:00
Platform: TestPlatform
NWBInspector version: 0.0.0

Scanned 1 file(s).
Found 1 issues across 1 file(s):
       1 - CRITICAL
**************************************************


0  CRITICAL
===========

0.0  /path/to/file.nwb: test_check - 'TestType' object at location '/test/location'
       Message: Test message
"""
        self.assertEqual(output, expected_output)

    @patch("nwbinspector._formatting._get_report_header")
    def test_markdown_formatter_complete_output(self, mock_header):
        """Test that MarkdownFormatter produces the exact expected Markdown output."""
        mock_header.return_value = {
            "Timestamp": "2024-01-01 00:00:00",
            "Platform": "TestPlatform",
            "NWBInspector_version": "0.0.0",
        }
        messages = [self._create_test_message()]
        levels = ["importance", "file_path"]
        nfiles_detected = 1

        formatter = MarkdownFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()
        output = "\n".join(formatted_messages)

        expected_output = """**************************************************
NWBInspector Report Summary

Timestamp: 2024-01-01 00:00:00
Platform: TestPlatform
NWBInspector version: 0.0.0

Scanned 1 file(s).
Found 1 issues across 1 file(s):
       1 - CRITICAL
**************************************************


# 0  CRITICAL

0.0  /path/to/file.nwb: test_check - 'TestType' object at location '/test/location'
       Message: Test message
"""
        self.assertEqual(output, expected_output)

    @patch("nwbinspector._formatting._get_report_header")
    def test_html_formatter_complete_output(self, mock_header):
        """Test that HtmlFormatter produces the exact expected HTML output."""
        mock_header.return_value = {
            "Timestamp": "2024-01-01 00:00:00",
            "Platform": "TestPlatform",
            "NWBInspector_version": "0.0.0",
        }
        messages = [self._create_test_message()]
        levels = ["importance", "file_path"]
        nfiles_detected = 1

        formatter = HtmlFormatter(
            messages=messages,
            levels=levels,
            nfiles_detected=nfiles_detected,
        )
        formatted_messages = formatter.format_messages()
        output = "\n".join(formatted_messages)

        expected_output = """<!DOCTYPE html>
<html>
<head>
    <meta charset='utf-8'>
    <title>NWBInspector Report</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 40px; background: #f8f9fa; }
        .summary { background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 30px; }
        .summary h1 { margin-top: 0; color: #333; }
        .summary-meta { color: #666; font-size: 14px; margin-bottom: 20px; }
        .summary-stats { background: #f8f9fa; padding: 15px; border-radius: 4px; }
        .importance-list { list-style: none; padding: 0; margin: 10px 0 0 0; }
        .importance-list li { padding: 5px 0; }
        .importance-count { font-weight: bold; color: #333; }
        .critical { color: #dc3545; }
        .best-practice-violation { color: #fd7e14; }
        .best-practice-suggestion { color: #ffc107; }
        h2 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; margin-top: 30px; }
        h3 { color: #555; margin-top: 20px; }
        .message { margin: 15px 0; padding: 15px; background: #fff; border-left: 4px solid #007bff; border-radius: 4px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .message-header { font-weight: 500; color: #333; }
        .message-content { color: #666; margin-top: 8px; }
    </style>
</head>
<body>
<div class='summary'>
    <h1>NWBInspector Report</h1>
    <div class='summary-meta'>
        <p><strong>Timestamp:</strong> 2024-01-01 00:00:00</p>
        <p><strong>Platform:</strong> TestPlatform</p>
        <p><strong>NWBInspector version:</strong> 0.0.0</p>
    </div>
    <div class='summary-stats'>
        <p>Scanned <strong>1</strong> file(s).</p>
        <p>Found <strong>1</strong> issues across <strong>1</strong> file(s):</p>
        <ul class='importance-list'>
            <li><span class='importance-count critical'>1</span> CRITICAL</li>
        </ul>
    </div>
</div>

<h2>0  CRITICAL</h2>

0.0  /path/to/file.nwb: test_check - 'TestType' object at location '/test/location'
       Message: Test message

</body>
</html>"""
        self.assertEqual(output, expected_output)
