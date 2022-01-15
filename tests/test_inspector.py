"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from collections import defaultdict
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector.refactor_inspector import inspect_nwb


class TestInspector(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )

    def tearDown(self):
        rmtree(self.tempdir)

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
        self.electrode_table_region = self.nwbfile.create_electrode_table_region(
            electrode_ids, description=""
        )

        n_bytes = 3e6
        # itemsize of 8 because of float dtype
        n_frames = int(n_bytes / (self.num_electrodes * 8))
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
        )
        self.nwbfile.add_acquisition(time_series)

    def add_flipped_data_orientation(self):
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

    def test_inspect_nwb(self):
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()
        self.add_flipped_data_orientation()
        self.add_non_matching_timestamps_dimension()

        nwbfile_path = str(self.tempdir / "testing.nwb")
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            check_results = inspect_nwb(nwbfile=written_nwbfile)

            regular_timestamp_series = written_nwbfile.acquisition["test_ecephys_2"]
            regular_timestamp_rate = (
                regular_timestamp_series.timestamps[1]
                - regular_timestamp_series.timestamps[0]
            )
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
            for severity, result_list in true_results.items():
                for result in result_list:
                    check_function_name = result["check_function_name"]
                    object_name = result["object_name"]
                    matched_dictionary = None
                    for index, check_result in enumerate(check_results[severity]):
                        if (
                            check_result["check_function_name"] == check_function_name
                            and check_result["object_name"] == object_name
                        ):
                            matched_dictionary = index
                    self.assertIsNotNone(obj=matched_dictionary)
                    print(check_results[severity][matched_dictionary])
                    print(result)
                    self.assertDictEqual(
                        d1=check_results[severity][matched_dictionary], d2=result
                    )
