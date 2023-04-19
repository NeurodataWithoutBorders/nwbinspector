import os
import pytest
from shutil import rmtree
from tempfile import mkdtemp
from pathlib import Path
from unittest import TestCase

from nwbinspector import Importance
from nwbinspector import inspect_all
from nwbinspector.register_checks import InspectorMessage
from nwbinspector.testing import check_streaming_tests_enabled
from nwbinspector.utils import FilePathType

STREAMING_TESTS_ENABLED, DISABLED_STREAMING_TESTS_REASON = check_streaming_tests_enabled()


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_dandiset_streaming():
    messages = list(inspect_all(path="000126", select=["check_subject_species_exists"], stream=True))
    assert messages[0] == InspectorMessage(
        message="Subject species is missing.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_subject_species_exists",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
        file_path="sub-1/sub-1.nwb",
    )


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_dandiset_streaming_parallel():
    messages = list(inspect_all(path="000126", select=["check_subject_species_exists"], stream=True, n_jobs=2))
    assert messages[0] == InspectorMessage(
        message="Subject species is missing.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_subject_species_exists",
        object_type="Subject",
        object_name="subject",
        location="/general/subject",
        file_path="sub-1/sub-1.nwb",
    )


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
class TestStreamingCLI(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = Path(mkdtemp())

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tempdir)

    def assertFileExists(self, path: FilePathType):
        path = Path(path)
        assert path.exists()

    def test_dandiset_streaming_cli(self):
        console_output_file = self.tempdir / "test_console_streaming_output_1.txt"
        os.system(
            f"nwbinspector 000126 --stream "
            f"--report-file-path {self.tempdir / 'test_nwbinspector_streaming_report_6.txt'}"
            f"> {console_output_file}"
        )
        self.assertFileExists(path=self.tempdir / "test_nwbinspector_streaming_report_6.txt")

    def test_dandiset_streaming_cli_parallel(self):
        console_output_file = self.tempdir / "test_console_streaming_output_2.txt"
        os.system(
            f"nwbinspector https://dandiarchive.org/dandiset/000126/0.210813.0327 --stream --n-jobs 2 "
            f"--report-file-path {self.tempdir / 'test_nwbinspector_streaming_report_7.txt'}"
            f"> {console_output_file}"
        )
        self.assertFileExists(path=self.tempdir / "test_nwbinspector_streaming_report_7.txt")
