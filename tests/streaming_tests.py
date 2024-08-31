"""All tests that specifically require streaming to be enabled (i.e., ROS3 version of h5py, fsspec, etc.)."""

import os
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

import pytest

from nwbinspector import Importance, InspectorMessage, inspect_all
from nwbinspector.testing import check_hdf5_io_open, check_streaming_tests_enabled
from nwbinspector.tools import read_nwbfile
from nwbinspector.utils import FilePathType

STREAMING_TESTS_ENABLED, DISABLED_STREAMING_TESTS_REASON = check_streaming_tests_enabled()
PERSISTENT_READ_NWBFILE_HDF5_EXAMPLE_HTTPS = (
    "https://dandi-api-staging-dandisets.s3.amazonaws.com/blobs/80d/80f/80d80f55-f8a1-4318-b17e-ce55f4dd2620"
)
PERSISTENT_READ_NWBFILE_HDF5_EXAMPLE_S3 = (
    "s3://dandi-api-staging-dandisets/blobs/80d/80f/80d80f55-f8a1-4318-b17e-ce55f4dd2620"
)
PERSISTENT_READ_NWBFILE_ZARR_EXAMPLE_HTTPS = (
    "https://dandi-api-staging-dandisets.s3.amazonaws.com/zarr/63f06140-8d0c-4db4-81cc-812ed4e4db03"
)
PERSISTENT_READ_NWBFILE_ZARR_EXAMPLE_S3 = "s3://dandi-api-staging-dandisets/zarr/63f06140-8d0c-4db4-81cc-812ed4e4db03"


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


# These will move to PyNWB when the time is right
@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_fsspec_https():
    nwbfile = read_nwbfile(
        nwbfile_path=PERSISTENT_READ_NWBFILE_HDF5_EXAMPLE_HTTPS,
        backend="hdf5",  # TODO: cannot current auto-detect backend when streaming
        method="fsspec",
    )
    assert check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    assert not check_hdf5_io_open(io=nwbfile.read_io)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_fsspec_s3():
    nwbfile = read_nwbfile(
        nwbfile_path=PERSISTENT_READ_NWBFILE_HDF5_EXAMPLE_S3,
        backend="hdf5",  # TODO: cannot current auto-detect backend when streaming
        method="fsspec",
    )
    assert check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    assert not check_hdf5_io_open(io=nwbfile.read_io)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_ros3_https():
    nwbfile = read_nwbfile(
        nwbfile_path=PERSISTENT_READ_NWBFILE_HDF5_EXAMPLE_HTTPS,
        backend="hdf5",  # TODO: cannot current auto-detect backend when streaming
        method="ros3",
    )
    assert check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    assert not check_hdf5_io_open(io=nwbfile.read_io)


# Zarr files not working yet with streaming

# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_fsspec_streaming_https():
#     nwbfile = read_nwbfile(
#         nwbfile_path=PERSISTENT_READ_NWBFILE_ZARR_EXAMPLE_HTTPS,
#         method="fsspec",
#     )
#     assert check_zarr_io_open(io=nwbfile.read_io)

#     nwbfile.read_io.close()
#     assert not check_zarr_io_open(io=nwbfile.read_io)


# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_fsspec_streaming_s3():
#     nwbfile = read_nwbfile(
#         nwbfile_path=PERSISTENT_READ_NWBFILE_ZARR_EXAMPLE_S3,
#         method="fsspec",
#     )
#     assert check_zarr_io_open(io=nwbfile.read_io)

#     nwbfile.read_io.close()
#     assert not check_zarr_io_open(io=nwbfile.read_io)


# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_ros3_error():
#     test that an error is raised with ros3 driver on zarr (not applicable)
