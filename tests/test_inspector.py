"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
<<<<<<< HEAD
from collections import defaultdict
=======
>>>>>>> squash_refactor_changelog
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path
<<<<<<< HEAD
from typing import Optional

import pynwb
import pytest
=======

import pytest
from pynwb import NWBFile, NWBHDF5IO, TimeSeries
>>>>>>> squash_refactor_changelog

from nwbinspector.nwbinspector import inspect_nwb


class TestInspector(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
<<<<<<< HEAD
        self.nwbfile = pynwb.NWBFile(
=======
        self.nwbfile = NWBFile(
>>>>>>> squash_refactor_changelog
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )

    def tearDown(self):
        rmtree(self.tempdir)

<<<<<<< HEAD
    def assertResultsEquivalent(self, test_result: dict, true_results: dict):
        for severity, result_list in true_results.items():
            for result in result_list:
                check_function_name = result["check_function_name"]
                object_name = result["object_name"]
                matched_dictionary = None
                for index, check_result in enumerate(test_result[severity]):
                    if (
                        check_result["check_function_name"] == check_function_name
                        and check_result["object_name"] == object_name
                    ):
                        matched_dictionary = index
                self.assertIsNotNone(obj=matched_dictionary)
                self.assertDictEqual(d1=test_result[severity][matched_dictionary], d2=result)

    def assertPostWriteResultsEquivalent(self, true_results: dict, inspect_nwb_kwargs: Optional[dict] = None):
        if inspect_nwb_kwargs is None:
            inspect_nwb_kwargs = dict()

        nwbfile_path = str(self.tempdir / "testing.nwb")
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            self.assertResultsEquivalent(
                test_result=inspect_nwb(nwbfile=written_nwbfile, **inspect_nwb_kwargs),
                true_results=true_results,
            )

    def add_big_dataset_no_compression(self):
        device = self.nwbfile.create_device(name="test_device")
        electrode_group = self.nwbfile.create_electrode_group(
            name="test_group", description="", location="", device=device
        )
        self.num_electrodes = 4
        electrode_ids = list(range(self.num_electrodes))
        for id in electrode_ids:
            self.nwbfile.add_electrode(
                id=id,
                x=np.nan,
                y=np.nan,
                z=np.nan,
                imp=np.nan,
                location="",
                filtering="",
                group=electrode_group,
            )
        self.electrode_table_region = self.nwbfile.create_electrode_table_region(electrode_ids, description="")

        n_frames = int(3e6 / (self.num_electrodes * np.dtype("float").itemsize))
        ephys_data = np.zeros(shape=(n_frames, self.num_electrodes))
        ephys_ts = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_1",
            data=ephys_data,
            electrodes=self.electrode_table_region,
            rate=10.0,
        )
        self.nwbfile.add_acquisition(ephys_ts)

    def add_regular_timestamps(self):
        time_series = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_2",
            data=np.zeros(shape=(5, self.num_electrodes)),
            electrodes=self.electrode_table_region,
            timestamps=np.arange(1.2, 11.2, 2),
=======
    def add_big_dataset_no_compression(self):
        time_series = TimeSeries(
            name="test_time_series_1", data=np.zeros(shape=int(3e6 / np.dtype("float").itemsize)), rate=1.0, unit=""
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
>>>>>>> squash_refactor_changelog
        )
        self.nwbfile.add_acquisition(time_series)

    def add_flipped_data_orientation(self):
<<<<<<< HEAD
        time_series = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_3",
            data=np.zeros(shape=(self.num_electrodes, 5)),
            electrodes=self.electrode_table_region,
            rate=1.0,
        )
        self.nwbfile.add_acquisition(time_series)

    def add_non_matching_timestamps_dimension(self):
        time_series = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_4",
            data=np.zeros(shape=(self.num_electrodes, 5)),
            electrodes=self.electrode_table_region,
            timestamps=np.arange(1.1, 6.1),
        )
        self.nwbfile.add_acquisition(time_series)

=======
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

    def run_inspect_nwb(self, **inspect_nwb_kwargs):
        nwbfile_path = str(self.tempdir / "testing.nwb")
        with NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            test_results = inspect_nwb(nwbfile=written_nwbfile, **inspect_nwb_kwargs)
        return test_results

>>>>>>> squash_refactor_changelog
    def test_inspect_nwb(self):
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()
        self.add_flipped_data_orientation()
        self.add_non_matching_timestamps_dimension()

<<<<<<< HEAD
        regular_timestamp_series = self.nwbfile.acquisition["test_ecephys_2"]
        regular_timestamp_rate = regular_timestamp_series.timestamps[1] - regular_timestamp_series.timestamps[0]
        true_results = defaultdict(
            list,
            {
                1: [
                    dict(
                        check_function_name="check_dataset_compression",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_1",
                        output="Consider enabling compression when writing a large dataset.",
                    )
                ],
                2: [
                    dict(
                        check_function_name="check_regular_timestamps",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_2",
                        output=(
                            "TimeSeries appears to have a constant sampling rate. "
                            f"Consider specifying starting_time={regular_timestamp_series.timestamps[0]} and "
                            f"rate={regular_timestamp_rate} instead of timestamps."
                        ),
                    ),
                    dict(
                        check_function_name="check_data_orientation",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_3",
                        output=(
                            "Data orientation may be in the wrong orientation. "
                            "Time should be in the first dimension, and is usually the longest dimension. "
                            "Here, another dimension is longer. "
                        ),
                    ),
                    dict(
                        check_function_name="check_data_orientation",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_4",
                        output=(
                            "Data orientation may be in the wrong orientation. "
                            "Time should be in the first dimension, and is usually the longest dimension. "
                            "Here, another dimension is longer. "
                        ),
                    ),
                ],
                3: [
                    dict(
                        check_function_name="check_timestamps_match_first_dimension",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_4",
                        output="The length of the first dimension of data does not match the length of timestamps.",
                    ),
                ],
            },
        )
        self.assertPostWriteResultsEquivalent(true_results=true_results)

    def test_inspect_nwb_severity_threshold(self):
=======
        test_results = self.run_inspect_nwb()
        true_results = [
            {
                "severity": "low",
                "message": "Consider enabling compression when writing a large dataset.",
                "importance": "Best Practice Violation",
                "check_function_name": "check_dataset_compression",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
            {
                "severity": "low",
                "message": "Consider enabling compression when writing a large dataset.",
                "importance": "Best Practice Violation",
                "check_function_name": "check_dataset_compression",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_3",
            },
            {
                "severity": "low",
                "message": "Consider enabling compression when writing a large dataset.",
                "importance": "Best Practice Violation",
                "check_function_name": "check_dataset_compression",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_2",
            },
            {
                "severity": "low",
                "message": "Consider enabling compression when writing a large dataset.",
                "importance": "Best Practice Violation",
                "check_function_name": "check_dataset_compression",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_1",
            },
            {
                "severity": "low",
                "message": (
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.0 and rate=1.0 instead of timestamps."
                ),
                "importance": "Best Practice Violation",
                "check_function_name": "check_regular_timestamps",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
            {
                "severity": "low",
                "message": (
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.2 and rate=2.0 instead of timestamps."
                ),
                "importance": "Best Practice Violation",
                "check_function_name": "check_regular_timestamps",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_2",
            },
            {
                "severity": "high",
                "message": (
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer. "
                ),
                "importance": "Critical",
                "check_function_name": "check_data_orientation",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
            {
                "severity": "high",
                "message": "The length of the first dimension of data does not match the length of timestamps.",
                "importance": "Critical",
                "check_function_name": "check_timestamps_match_first_dimension",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
        ]
        self.assertListEqual(list1=test_results, list2=true_results)

    def test_inspect_nwb_importance_threshold(self):
>>>>>>> squash_refactor_changelog
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()
        self.add_flipped_data_orientation()
        self.add_non_matching_timestamps_dimension()

<<<<<<< HEAD
        true_results = defaultdict(
            list,
            {
                3: [
                    dict(
                        check_function_name="check_timestamps_match_first_dimension",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_4",
                        output="The length of the first dimension of data does not match the length of timestamps.",
                    ),
                ],
            },
        )
        self.assertPostWriteResultsEquivalent(true_results=true_results, inspect_nwb_kwargs=dict(severity_threshold=2))
=======
        test_results = self.run_inspect_nwb(importance_threshold="Critical")
        true_results = [
            {
                "severity": "high",
                "message": (
                    "Data may be in the wrong orientation. Time should be in the first dimension, and is "
                    "usually the longest dimension. Here, another dimension is longer. "
                ),
                "importance": "Critical",
                "check_function_name": "check_data_orientation",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
            {
                "severity": "high",
                "message": "The length of the first dimension of data does not match the length of timestamps.",
                "importance": "Critical",
                "check_function_name": "check_timestamps_match_first_dimension",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
        ]
        self.assertListEqual(list1=test_results, list2=true_results)
>>>>>>> squash_refactor_changelog

    def test_inspect_nwb_skip(self):
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()
        self.add_flipped_data_orientation()
        self.add_non_matching_timestamps_dimension()

<<<<<<< HEAD
        regular_timestamp_series = self.nwbfile.acquisition["test_ecephys_2"]
        regular_timestamp_rate = regular_timestamp_series.timestamps[1] - regular_timestamp_series.timestamps[0]
        true_results = defaultdict(
            list,
            {
                1: [
                    dict(
                        check_function_name="check_dataset_compression",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_1",
                        output="Consider enabling compression when writing a large dataset.",
                    )
                ],
                2: [
                    dict(
                        check_function_name="check_regular_timestamps",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_2",
                        output=(
                            "TimeSeries appears to have a constant sampling rate. "
                            f"Consider specifying starting_time={regular_timestamp_series.timestamps[0]} and "
                            f"rate={regular_timestamp_rate} instead of timestamps."
                        ),
                    )
                ],
                3: [
                    dict(
                        check_function_name="check_timestamps_match_first_dimension",
                        object_type="ElectricalSeries",
                        object_name="test_ecephys_4",
                        output="The length of the first dimension of data does not match the length of timestamps.",
                    ),
                ],
            },
        )
        self.assertPostWriteResultsEquivalent(
            true_results=true_results,
            inspect_nwb_kwargs=dict(skip=["check_data_orientation"]),
        )
=======
        test_results = self.run_inspect_nwb(skip=["check_data_orientation", "check_dataset_compression"])
        true_results = [
            {
                "severity": "low",
                "message": (
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.0 and rate=1.0 instead of timestamps."
                ),
                "importance": "Best Practice Violation",
                "check_function_name": "check_regular_timestamps",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
            {
                "severity": "low",
                "message": (
                    "TimeSeries appears to have a constant sampling rate. Consider specifying "
                    "starting_time=1.2 and rate=2.0 instead of timestamps."
                ),
                "importance": "Best Practice Violation",
                "check_function_name": "check_regular_timestamps",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_2",
            },
            {
                "severity": "high",
                "message": "The length of the first dimension of data does not match the length of timestamps.",
                "importance": "Critical",
                "check_function_name": "check_timestamps_match_first_dimension",
                "object_type": "TimeSeries",
                "object_name": "test_time_series_4",
            },
        ]
        self.assertListEqual(list1=test_results, list2=true_results)
>>>>>>> squash_refactor_changelog

    @pytest.mark.skip(msg="TODO")
    def test_cmd_line(self):
        pass
