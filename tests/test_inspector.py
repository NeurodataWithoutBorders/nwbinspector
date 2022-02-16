import os
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path
from typing import List
from collections import OrderedDict, defaultdict

from pynwb import NWBFile, NWBHDF5IO, TimeSeries
from pynwb.behavior import SpatialSeries, Position

from nwbinspector import (
    Importance,
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)
from nwbinspector.nwbinspector import inspect_nwb
from nwbinspector.register_checks import Severity, InspectorMessage
from nwbinspector.utils import FilePathType


def add_big_dataset_no_compression(nwbfile):
    time_series = TimeSeries(
        name="test_time_series_1", data=np.zeros(shape=int(1.1e9 / np.dtype("float").itemsize)), rate=1.0, unit=""
    )
    nwbfile.add_acquisition(time_series)


def add_regular_timestamps(nwbfile):
    regular_timestamps = np.arange(1.2, 11.2, 2)
    timestamps_length = len(regular_timestamps)
    time_series = TimeSeries(
        name="test_time_series_2",
        data=np.zeros(shape=(timestamps_length, timestamps_length - 1)),
        timestamps=regular_timestamps,
        unit="",
    )
    nwbfile.add_acquisition(time_series)


def add_flipped_data_orientation_to_processing(nwbfile):
    spatial_series = SpatialSeries(
        name="my_spatial_series", data=np.zeros(shape=(2, 3)), reference_frame="unknown", rate=1.0
    )
    module = nwbfile.create_processing_module(name="behavior", description="")
    module.add(Position(spatial_series=spatial_series))


def add_non_matching_timestamps_dimension(nwbfile):
    timestamps = [1.0, 2.1, 3.0]
    timestamps_length = len(timestamps)
    time_series = TimeSeries(
        name="test_time_series_3",
        data=np.zeros(shape=(timestamps_length + 1, timestamps_length)),
        timestamps=timestamps,
        unit="",
    )
    nwbfile.add_acquisition(time_series)


class TestInspector(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = Path(mkdtemp())
        # cls.tempdir = Path("E:/test_inspector/test")
        check_list = [
            check_dataset_compression,
            check_regular_timestamps,
            check_data_orientation,
            check_timestamps_match_first_dimension,
        ]
        cls.checks = OrderedDict({importance: defaultdict(list) for importance in Importance})
        for check in check_list:
            cls.checks[check.importance][check.neurodata_type].append(check)
        num_nwbfiles = 4
        nwbfiles = list()
        for j in range(num_nwbfiles):
            nwbfiles.append(
                NWBFile(
                    session_description="Testing inspector.",
                    identifier=str(uuid4()),
                    session_start_time=datetime.now().astimezone(),
                )
            )
        add_regular_timestamps(nwbfiles[0])
        add_flipped_data_orientation_to_processing(nwbfiles[0])
        add_non_matching_timestamps_dimension(nwbfiles[0])
        add_regular_timestamps(nwbfiles[1])
        # Last file to be left without violations

        cls.nwbfile_paths = [cls.tempdir / f"testing{j}.nwb" for j in range(num_nwbfiles)]
        for nwbfile_path, nwbfile in zip(cls.nwbfile_paths, nwbfiles):
            with NWBHDF5IO(path=str(nwbfile_path), mode="w") as io:
                io.write(nwbfile)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tempdir)

    def assertListofDictEqual(self, test_list: List[dict], true_list: List[dict]):
        for dictionary in test_list:
            self.assertIn(member=dictionary, container=true_list)
        for dictionary in true_list:
            self.assertIn(member=dictionary, container=test_list)

    def assertFileExists(self, path: FilePathType):
        path = Path(path)
        assert path.exists()

    def assertLogFileContentsEqual(self, test_file_path: FilePathType, true_file_path: FilePathType):
        with open(file=test_file_path, mode="r") as test_file:
            with open(file=true_file_path, mode="r") as true_file:
                test_file_lines = test_file.readlines()
                true_file_lines = true_file.readlines()
                for line_number, test_line in enumerate(test_file_lines):
                    if "NWBFile: " in test_line:
                        # Transform temporary testing path and formatted to hardcoded fake path
                        test_file_lines[line_number] = f"NWBFile: /home/fake_path/{test_line[-13:]}"
                        test_file_lines[line_number + 1] = "=" * (len(test_file_lines[line_number]) - 1) + "\n"
                self.assertEqual(first=test_file_lines, second=true_file_lines)

    def test_inspect_nwb(self):
        with NWBHDF5IO(path=self.nwbfile_paths[0], mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(nwbfile=written_nwbfile, checks=self.checks)
        true_results = [
            InspectorMessage(
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is usually "
                    "the longest dimension. Here, another dimension is longer."
                ),
                severity=Severity.NO_SEVERITY,
                importance=Importance.CRITICAL,
                check_function_name="check_data_orientation",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
            ),
            InspectorMessage(
                message="The length of the first dimension of data does not match the length of timestamps.",
                severity=Severity.NO_SEVERITY,
                importance=Importance.CRITICAL,
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
            ),
            InspectorMessage(
                message="Consider enabling compression when writing a large dataset.",
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_dataset_compression",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
            ),
            InspectorMessage(
                message="Consider enabling compression when writing a large dataset.",
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
            ),
            InspectorMessage(
                message="Consider enabling compression when writing a large dataset.",
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_2",
                location="/acquisition/",
            ),
            InspectorMessage(
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 "
                    "and rate=2.0 instead of timestamps."
                ),
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
                location="/acquisition/",
            ),
        ]
        self.assertListofDictEqual(test_list=test_results, true_list=true_results)

    def test_inspect_nwb_importance_threshold(self):
        with NWBHDF5IO(path=self.nwbfile_paths[0], mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(
                nwbfile=written_nwbfile, checks=self.checks, importance_threshold=Importance.CRITICAL
            )
        true_results = [
            InspectorMessage(
                severity=Severity.NO_SEVERITY,
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer."
                ),
                importance=Importance.CRITICAL,
                check_function_name="check_data_orientation",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
            ),
            InspectorMessage(
                severity=Severity.NO_SEVERITY,
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance=Importance.CRITICAL,
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
            ),
        ]
        self.assertListofDictEqual(test_list=test_results, true_list=true_results)

    def test_command_line_runs(self):
        os.system(f"nwbinspector {str(self.nwbfile_paths[0])}")
        self.assertFileExists(path="nwbinspector_log_file.txt")

    def test_command_line_on_directory_matches_file(self):
        os.system(
            f"nwbinspector {str(self.tempdir)} -o -s check_timestamps_match_first_dimension,check_data_orientation,"
            f"check_regular_timestamps,check_dataset_compression"
        )
        self.assertLogFileContentsEqual(
            test_file_path="nwbinspector_log_file.txt",
            true_file_path=Path(__file__).parent / "true_nwbinspector_log_file.txt",
        )
