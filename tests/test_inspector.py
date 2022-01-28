"""Authors: Cody Baker and Ben Dichter."""
import os
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import Union, List

from pynwb import NWBFile, NWBHDF5IO, TimeSeries

from nwbinspector.nwbinspector import inspect_nwb

FilePathType = Union[Path, str]


class TestInspector(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()
        self.add_flipped_data_orientation()
        self.add_non_matching_timestamps_dimension()

        self.nwbfile_path = self.tempdir / "testing.nwb"
        with NWBHDF5IO(path=str(self.nwbfile_path), mode="w") as io:
            io.write(self.nwbfile)

    def tearDown(self):
        rmtree(self.tempdir)

    def add_big_dataset_no_compression(self):
        time_series = TimeSeries(
            name="test_time_series_1", data=np.zeros(shape=int(1.1e9 / np.dtype("float").itemsize)), rate=1.0, unit=""
        )
        self.nwbfile.add_acquisition(time_series)

    def add_regular_timestamps(self):
        regular_timestamps = np.arange(1.2, 11.2, 2)
        timestamps_length = len(regular_timestamps)
        time_series = TimeSeries(
            name="test_time_series_2",
            data=np.zeros(shape=(timestamps_length, timestamps_length - 1)),
            timestamps=regular_timestamps,
            unit="",
        )
        self.nwbfile.add_acquisition(time_series)

    def add_flipped_data_orientation(self):
        time_series = TimeSeries(name="test_time_series_3", data=np.zeros(shape=(5, 3)), rate=1.0, unit="")
        self.nwbfile.add_acquisition(time_series)

    def add_non_matching_timestamps_dimension(self):
        timestamps = [1.0, 2.0, 3.0]
        timestamps_length = len(timestamps)
        time_series = TimeSeries(
            name="test_time_series_4",
            data=np.zeros(shape=(timestamps_length - 1, timestamps_length)),
            timestamps=timestamps,
            unit="",
        )
        self.nwbfile.add_acquisition(time_series)

    def assertListofDictEqual(self, test_list: List[dict], true_list: List[dict]):
        for dictionary in test_list:
            self.assertIn(member=dictionary, container=true_list)
        for dictionary in true_list:
            self.assertIn(member=dictionary, container=test_list)

    def assertFileExists(self, path: FilePathType):
        assert path.exists()

    def assertFileContentsEqual(self, test_file_path: FilePathType, true_file_path: FilePathType):
        with open(file=test_file_path, mode="r") as test_file:
            with open(file=true_file_path, mode="r") as true_file:
                assert test_file.readlines() == true_file.readlines()

    def test_inspect_nwb(self):
        with NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(nwbfile=written_nwbfile)
        true_results = [
            dict(
                severity="LOW_SEVERITY",
                message="Consider enabling compression when writing a large dataset.",
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
            dict(
                severity="LOW_SEVERITY",
                message="Consider enabling compression when writing a large dataset.",
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_3",
            ),
            dict(
                severity="LOW_SEVERITY",
                message="Consider enabling compression when writing a large dataset.",
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_2",
            ),
            dict(
                severity="HIGH_SEVERITY",
                message="Consider enabling compression when writing a large dataset.",
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_1",
            ),
            dict(
                severity="LOW_SEVERITY",
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.0 and "
                    "rate=1.0 instead of timestamps."
                ),
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
            dict(
                severity="LOW_SEVERITY",
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.2 and rate=2.0 instead of timestamps."
                ),
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
            ),
            dict(
                severity=None,
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer. "
                ),
                importance="CRITICAL_IMPORTANCE",
                check_function_name="check_data_orientation",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
            dict(
                severity=None,
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance="CRITICAL_IMPORTANCE",
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
        ]
        self.assertListofDictEqual(test_list=test_results, true_list=true_results)

    def test_inspect_nwb_importance_threshold(self):
        with NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(nwbfile=written_nwbfile, importance_threshold="CRITICAL_IMPORTANCE")
        true_results = [
            dict(
                severity=None,
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer. "
                ),
                importance="CRITICAL_IMPORTANCE",
                check_function_name="check_data_orientation",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
            dict(
                severity=None,
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance="CRITICAL_IMPORTANCE",
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
        ]
        self.assertListofDictEqual(test_list=test_results, true_list=true_results)

    def test_inspect_nwb_skip(self):
        with NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(
                nwbfile=written_nwbfile, skip=["check_data_orientation", "check_dataset_compression"]
            )
        true_results = [
            dict(
                severity="LOW_SEVERITY",
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.0 and "
                    "rate=1.0 instead of timestamps."
                ),
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
            dict(
                severity="LOW_SEVERITY",
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.2 and rate=2.0 instead of timestamps."
                ),
                importance="BEST_PRACTICE_VIOLATION",
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
            ),
            dict(
                severity=None,
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance="CRITICAL_IMPORTANCE",
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_4",
            ),
        ]
        self.assertListofDictEqual(test_list=test_results, true_list=true_results)

    def test_command_line_runs(self):
        os.system(f"nwbinspector {str(self.nwbfile_path)}")
        self.assertFileExists(path=self.nwbfile_path.parent / f"nwbinspector_log_file_{self.nwbfile_path.stem}.txt")

    def test_command_line_matches_file(self):
        os.system(f"nwbinspector {str(self.nwbfile_path)}")
        self.assertFileContentsEqual(
            test_file_path=self.nwbfile_path.parent / f"nwbinspector_log_file_{self.nwbfile_path.stem}.txt",
            true_file_path=Path(__file__).parent / f"true_nwbinspector_log_file_{self.nwbfile_path.stem}.txt",
        )
