"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector.check_time_series import (
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)


class TestTimeSeriesChecks(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )
        self.nwbfile_path = str(self.tempdir / "testing.nwb")

    def tearDown(self):
        rmtree(self.tempdir)

    def test_check_dataset_compression(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_unit",
            data=np.zeros(shape=int(3e6 / np.dtype("float").itemsize)),
            rate=1.0,
        )

        output_message_1 = check_dataset_compression(time_series=time_series)
        self.assertEqual(first=output_message_1, second=None)

        self.nwbfile.add_acquisition(time_series)
        output_message_2 = check_dataset_compression(
            time_series=self.nwbfile.acquisition["test_time_series"]
        )
        self.assertEqual(first=output_message_2, second=None)

        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            output_message_3 = check_dataset_compression(
                time_series=written_nwbfile.acquisition["test_time_series"]
            )
            self.assertEqual(
                first=output_message_3,
                second="Consider enabling compression when writing a large dataset.",
            )

    def test_check_regular_timestamps(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
        true_message = (
            "TimeSeries appears to have a constant sampling rate. "
            f"Consider specifying starting_time={time_series.timestamps[0]} "
            f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
        )

        output_message_1 = check_regular_timestamps(time_series=time_series)
        self.assertEqual(first=output_message_1, second=true_message)

        self.nwbfile.add_acquisition(time_series)
        output_message_2 = check_regular_timestamps(
            time_series=self.nwbfile.acquisition["test_time_series"]
        )
        self.assertEqual(first=output_message_2, second=true_message)

        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            output_message_3 = check_regular_timestamps(
                time_series=written_nwbfile.acquisition["test_time_series"]
            )
            self.assertEqual(first=output_message_3, second=true_message)

    def test_check_data_orientation(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=(2, 100)),
            rate=1.0,
        )
        true_message = (
            "Data orientation may be in the wrong orientation. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer. "
        )

        output_message_1 = check_data_orientation(time_series=time_series)
        self.assertEqual(first=output_message_1, second=true_message)

        self.nwbfile.add_acquisition(time_series)
        output_message_2 = check_data_orientation(
            time_series=self.nwbfile.acquisition["test_time_series"]
        )
        self.assertEqual(first=output_message_2, second=true_message)

        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            output_message_3 = check_data_orientation(
                time_series=written_nwbfile.acquisition["test_time_series"]
            )
            self.assertEqual(first=output_message_3, second=true_message)

    def test_check_timestamps_match_first_dimension_1d(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=4),
            timestamps=[1.0, 2.0, 3.0],
        )
        true_message = "The length of the first dimension of data does not match the length of timestamps."

        output_message_1 = check_timestamps_match_first_dimension(
            time_series=time_series
        )
        self.assertEqual(first=output_message_1, second=true_message)

        self.nwbfile.add_acquisition(time_series)
        output_message_2 = check_timestamps_match_first_dimension(
            time_series=self.nwbfile.acquisition["test_time_series"]
        )
        self.assertEqual(first=output_message_2, second=true_message)

        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            output_message_3 = check_timestamps_match_first_dimension(
                time_series=written_nwbfile.acquisition["test_time_series"]
            )
            self.assertEqual(first=output_message_3, second=true_message)

    def test_check_timestamps_match_first_dimension_2d(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=(2, 3)),
            timestamps=[1.0, 2.0, 3.0],
        )
        true_message = "The length of the first dimension of data does not match the length of timestamps."

        output_message_1 = check_timestamps_match_first_dimension(
            time_series=time_series
        )
        self.assertEqual(first=output_message_1, second=true_message)

        self.nwbfile.add_acquisition(time_series)
        output_message_2 = check_timestamps_match_first_dimension(
            time_series=self.nwbfile.acquisition["test_time_series"]
        )
        self.assertEqual(first=output_message_2, second=true_message)

        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            output_message_3 = check_timestamps_match_first_dimension(
                time_series=written_nwbfile.acquisition["test_time_series"]
            )
            self.assertEqual(first=output_message_3, second=true_message)
