import os
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from pathlib import Path
from typing import List

import numpy as np
from pynwb import NWBFile, NWBHDF5IO, TimeSeries
from pynwb.file import TimeIntervals
from pynwb.behavior import SpatialSeries, Position
from hdmf.common import DynamicTable

from nwbinspector import (
    Importance,
    check_small_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)
from nwbinspector.nwbinspector import inspect_all, inspect_nwb, configure_checks
from nwbinspector.register_checks import Severity, InspectorMessage, register_check
from nwbinspector.utils import FilePathType
from nwbinspector.tools import make_minimal_nwbfile


def add_big_dataset_no_compression(nwbfile: NWBFile):
    time_series = TimeSeries(
        name="test_time_series_1", data=np.zeros(shape=int(1.1e9 / np.dtype("float").itemsize)), rate=1.0, unit=""
    )
    nwbfile.add_acquisition(time_series)


def add_regular_timestamps(nwbfile: NWBFile):
    regular_timestamps = np.arange(1.2, 11.2, 2)
    timestamps_length = len(regular_timestamps)
    time_series = TimeSeries(
        name="test_time_series_2",
        data=np.zeros(shape=(timestamps_length, timestamps_length - 1)),
        timestamps=regular_timestamps,
        unit="",
    )
    nwbfile.add_acquisition(time_series)


def add_flipped_data_orientation_to_processing(nwbfile: NWBFile):
    spatial_series = SpatialSeries(
        name="my_spatial_series", data=np.zeros(shape=(2, 3)), reference_frame="unknown", rate=1.0
    )
    module = nwbfile.create_processing_module(name="behavior", description="")
    module.add(Position(spatial_series=spatial_series))


def add_non_matching_timestamps_dimension(nwbfile: NWBFile):
    timestamps = [1.0, 2.1, 3.0]
    timestamps_length = len(timestamps)
    time_series = TimeSeries(
        name="test_time_series_3",
        data=np.zeros(shape=(timestamps_length + 1, timestamps_length)),
        timestamps=timestamps,
        unit="",
    )
    nwbfile.add_acquisition(time_series)


def add_simple_table(nwbfile: NWBFile):
    time_intervals = TimeIntervals(name="test_table", description="desc")
    time_intervals.add_row(start_time=2.0, stop_time=3.0)
    time_intervals.add_row(start_time=1.0, stop_time=2.0)
    nwbfile.add_acquisition(time_intervals)


class TestInspector(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = Path(mkdtemp())
        cls.checks = [
            check_small_dataset_compression,
            check_regular_timestamps,
            check_data_orientation,
            check_timestamps_match_first_dimension,
        ]
        num_nwbfiles = 2
        nwbfiles = list()
        for j in range(num_nwbfiles):
            nwbfiles.append(make_minimal_nwbfile())
        add_big_dataset_no_compression(nwbfiles[0])
        add_regular_timestamps(nwbfiles[0])
        add_flipped_data_orientation_to_processing(nwbfiles[0])
        add_non_matching_timestamps_dimension(nwbfiles[0])
        add_simple_table(nwbfiles[0])
        add_regular_timestamps(nwbfiles[1])
        # Last file to be left without violations

        cls.nwbfile_paths = [str(cls.tempdir / f"testing{j}.nwb") for j in range(num_nwbfiles)]
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

    def assertListsEquivalent(self, test_list: list, true_list: list):
        for member in test_list:
            self.assertIn(member=member, container=true_list)
        for member in true_list:
            self.assertIn(member=member, container=test_list)

    def assertFileExists(self, path: FilePathType):
        path = Path(path)
        assert path.exists()

    def assertLogFileContentsEqual(
        self, test_file_path: FilePathType, true_file_path: FilePathType, skip_first_newlines: bool = False
    ):
        with open(file=test_file_path, mode="r") as test_file:
            with open(file=true_file_path, mode="r") as true_file:
                test_file_lines = test_file.readlines()
                if skip_first_newlines:
                    for line_number, test_line in enumerate(test_file_lines):
                        if "NWBFile: " in test_line:
                            skip_first_n_lines = line_number
                            break
                else:
                    skip_first_n_lines = 0
                true_file_lines = true_file.readlines()
                for line_number, test_line in enumerate(test_file_lines):
                    if "NWBFile: " in test_line:
                        # Transform temporary testing path and formatted to hardcoded fake path
                        test_file_lines[line_number] = f"NWBFile: /home/fake_path/{test_line[-13:]}"
                        test_file_lines[line_number + 1] = "=" * (len(test_file_lines[line_number]) - 1) + "\n"
                self.assertEqual(first=test_file_lines[skip_first_n_lines:], second=true_file_lines)

    def test_inspect_all(self):
        test_results = list(inspect_all(path=self.tempdir, select=[x.__name__ for x in self.checks]))
        true_results = [
            InspectorMessage(
                message="data is not compressed. Consider enabling compression when writing a dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                severity=Severity.LOW,
                check_function_name="check_small_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_1",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 "
                    "and rate=2.0 instead of timestamps."
                ),
                importance=Importance.BEST_PRACTICE_VIOLATION,
                severity=Severity.LOW,
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is usually "
                    "the longest dimension. Here, another dimension is longer."
                ),
                importance=Importance.CRITICAL,
                severity=Severity.LOW,
                check_function_name="check_data_orientation",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance=Importance.CRITICAL,
                severity=Severity.LOW,
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 "
                    "and rate=2.0 instead of timestamps."
                ),
                importance=Importance.BEST_PRACTICE_VIOLATION,
                severity=Severity.LOW,
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
                location="/acquisition/",
                file="testing1.nwb",
            ),
        ]
        self.assertListsEquivalent(test_list=test_results, true_list=true_results)

        def test_inspect_all_parallel(self):
            test_results = []
            for test_result in inspect_all(
                path=Path(self.nwbfile_paths[0]).parent, select=[x.__name__ for x in self.checks], n_jobs=2
            ):
                test_results.extend(test_result)
            true_results = [
                InspectorMessage(
                    message="data is not compressed. Consider enabling compression when writing a dataset.",
                    importance=Importance.BEST_PRACTICE_SUGGESTION,
                    severity=Severity.LOW,
                    check_function_name="check_small_dataset_compression",
                    object_type="TimeSeries",
                    object_name="test_time_series_1",
                    location="/acquisition/",
                    file="testing0.nwb",
                ),
                InspectorMessage(
                    message=(
                        "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 "
                        "and rate=2.0 instead of timestamps."
                    ),
                    importance=Importance.BEST_PRACTICE_VIOLATION,
                    severity=Severity.LOW,
                    check_function_name="check_regular_timestamps",
                    object_type="TimeSeries",
                    object_name="test_time_series_2",
                    location="/acquisition/",
                    file="testing0.nwb",
                ),
                InspectorMessage(
                    message=(
                        "Data may be in the wrong orientation. Time should be in the first dimension, and is usually "
                        "the longest dimension. Here, another dimension is longer."
                    ),
                    importance=Importance.CRITICAL,
                    severity=Severity.LOW,
                    check_function_name="check_data_orientation",
                    object_type="SpatialSeries",
                    object_name="my_spatial_series",
                    location="/processing/behavior/Position/",
                    file="testing0.nwb",
                ),
                InspectorMessage(
                    message="The length of the first dimension of data does not match the length of timestamps.",
                    importance=Importance.CRITICAL,
                    severity=Severity.LOW,
                    check_function_name="check_timestamps_match_first_dimension",
                    object_type="TimeSeries",
                    object_name="test_time_series_3",
                    location="/acquisition/",
                    file="testing0.nwb",
                ),
                InspectorMessage(
                    message=(
                        "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 "
                        "and rate=2.0 instead of timestamps."
                    ),
                    importance=Importance.BEST_PRACTICE_VIOLATION,
                    severity=Severity.LOW,
                    check_function_name="check_regular_timestamps",
                    object_type="TimeSeries",
                    object_name="test_time_series_2",
                    location="/acquisition/",
                    file="testing1.nwb",
                ),
            ]
            self.assertListsEquivalent(test_list=test_results, true_list=true_results)

    def test_inspect_nwb(self):
        test_results = list(inspect_nwb(nwbfile_path=self.nwbfile_paths[0], checks=self.checks))
        true_results = [
            InspectorMessage(
                message="data is not compressed. Consider enabling compression when writing a dataset.",
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_small_dataset_compression",
                object_type="TimeSeries",
                object_name="test_time_series_1",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message=(
                    "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 and "
                    "rate=2.0 instead of timestamps."
                ),
                severity=Severity.LOW,
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_regular_timestamps",
                object_type="TimeSeries",
                object_name="test_time_series_2",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is usually the "
                    "longest dimension. Here, another dimension is longer."
                ),
                importance=Importance.CRITICAL,
                check_function_name="check_data_orientation",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance=Importance.CRITICAL,
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
                file="testing0.nwb",
            ),
        ]
        self.assertListsEquivalent(test_list=test_results, true_list=true_results)

    def test_inspect_nwb_importance_threshold(self):
        test_results = list(
            inspect_nwb(
                nwbfile_path=self.nwbfile_paths[0], checks=self.checks, importance_threshold=Importance.CRITICAL
            )
        )
        true_results = [
            InspectorMessage(
                message=(
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer."
                ),
                importance=Importance.CRITICAL,
                check_function_name="check_data_orientation",
                object_type="SpatialSeries",
                object_name="my_spatial_series",
                location="/processing/behavior/Position/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message="The length of the first dimension of data does not match the length of timestamps.",
                importance=Importance.CRITICAL,
                check_function_name="check_timestamps_match_first_dimension",
                object_type="TimeSeries",
                object_name="test_time_series_3",
                location="/acquisition/",
                file="testing0.nwb",
            ),
        ]
        self.assertListsEquivalent(test_list=test_results, true_list=true_results)

    def test_command_line_runs_cli_only(self):
        console_output_file = self.tempdir / "test_console_output.txt"
        os.system(
            f"nwbinspector {str(self.tempdir)} -o -s check_timestamps_match_first_dimension,"
            f"check_data_orientation,check_regular_timestamps,check_small_dataset_compression --no-color "
            f"> {console_output_file}"
        )
        self.assertLogFileContentsEqual(
            test_file_path=console_output_file,
            true_file_path=Path(__file__).parent / "true_nwbinspector_report.txt",
            skip_first_newlines=True,
        )

    def test_command_line_runs_saves_report(self):
        os.system(
            f"nwbinspector {str(self.nwbfile_paths[0])} --report-file-path {self.tempdir / 'nwbinspector_report.txt'}"
        )
        self.assertFileExists(path=self.tempdir / "nwbinspector_report.txt")

    def test_command_line_runs_saves_json(self):
        json_fpath = self.tempdir / "nwbinspector_results.json"
        os.system(f"nwbinspector {str(self.nwbfile_paths[0])} --json-file-path {json_fpath}")
        self.assertFileExists(path=json_fpath)

    def test_command_line_on_directory_matches_file(self):
        os.system(
            f"nwbinspector {str(self.tempdir)} -o -s check_timestamps_match_first_dimension,check_data_orientation,"
            f"check_regular_timestamps,check_small_dataset_compression"
            f" --report-file-path {self.tempdir / 'nwbinspector_report.txt'}"
        )
        self.assertLogFileContentsEqual(
            test_file_path=self.tempdir / "nwbinspector_report.txt",
            true_file_path=Path(__file__).parent / "true_nwbinspector_report.txt",
        )

    def test_iterable_check_function(self):
        @register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
        def iterable_check_function(table: DynamicTable):
            for col in table.columns:
                yield InspectorMessage(message=f"Column: {col.name}")

        test_results = list(inspect_nwb(nwbfile_path=self.nwbfile_paths[0], select=["iterable_check_function"]))
        print(test_results)
        true_results = [
            InspectorMessage(
                message="Column: start_time",
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="iterable_check_function",
                object_type="TimeIntervals",
                object_name="test_table",
                location="/acquisition/",
                file="testing0.nwb",
            ),
            InspectorMessage(
                message="Column: stop_time",
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="iterable_check_function",
                object_type="TimeIntervals",
                object_name="test_table",
                location="/acquisition/",
                file="testing0.nwb",
            ),
        ]
        self.assertListsEquivalent(test_list=test_results, true_list=true_results)


def test_configure_checks():

    # checks are moved
    checks = [
        check_small_dataset_compression,
        check_regular_timestamps,
        check_data_orientation,
        check_timestamps_match_first_dimension,
    ]
    config = {"CRITICAL": ["check_data_orientation"], "BEST_PRACTICE_SUGGESTION": ["check_regular_timestamps"]}

    out = configure_checks(checks=checks, config=config)

    assert out[2].importance is Importance.CRITICAL
    assert out[1].importance is Importance.BEST_PRACTICE_SUGGESTION

    # checks in same place are not moved
    config = {"CRITICAL": ["check_regular_timestamps"]}

    out = configure_checks(checks=checks, config=config)

    assert out[1].importance is Importance.CRITICAL
