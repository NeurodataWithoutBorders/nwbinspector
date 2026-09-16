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


def test_save_report_existing_file_message_names_overwrite_flag(tmp_path):
    """The message used to point at a '-o' flag that the CLI does not have."""
    import pytest

    from nwbinspector import save_report

    report_file_path = tmp_path / "report.txt"
    report_file_path.write_text("existing")

    with pytest.raises(FileExistsError, match="--overwrite"):
        save_report(report_file_path=report_file_path, formatted_messages=[], overwrite=False)


def test_cli_existing_json_file_message_names_overwrite_flag(tmp_path):
    """The existence check runs before the inspection, so no NWB file is needed to reach it."""
    from click.testing import CliRunner

    from nwbinspector._nwbinspector_cli import _nwbinspector_cli

    json_file_path = tmp_path / "report.json"
    json_file_path.write_text("{}")

    result = CliRunner().invoke(_nwbinspector_cli, [str(tmp_path), "--json-file-path", str(json_file_path)])

    assert isinstance(result.exception, FileExistsError)
    assert "--overwrite" in str(result.exception)
    assert "-o'" not in str(result.exception)


def test_cli_existing_report_file_message_names_overwrite_flag(tmp_path):
    from click.testing import CliRunner

    from nwbinspector._nwbinspector_cli import _nwbinspector_cli

    report_file_path = tmp_path / "report.txt"
    report_file_path.write_text("existing")

    result = CliRunner().invoke(_nwbinspector_cli, [str(tmp_path), "--report-file-path", str(report_file_path)])

    assert isinstance(result.exception, FileExistsError)
    assert "--overwrite" in str(result.exception)


def test_cli_overwrite_flag_allows_existing_output_files(tmp_path):
    """With --overwrite the up-front check passes and both files are written, here for an empty folder."""
    from click.testing import CliRunner

    from nwbinspector._nwbinspector_cli import _nwbinspector_cli

    json_file_path = tmp_path / "report.json"
    json_file_path.write_text("{}")
    report_file_path = tmp_path / "report.txt"
    report_file_path.write_text("existing")

    result = CliRunner().invoke(
        _nwbinspector_cli,
        [
            str(tmp_path),
            "--json-file-path",
            str(json_file_path),
            "--report-file-path",
            str(report_file_path),
            "--overwrite",
        ],
    )

    assert result.exception is None, result.output
    assert json_file_path.read_text() != "{}"
    assert report_file_path.read_text() != "existing"
