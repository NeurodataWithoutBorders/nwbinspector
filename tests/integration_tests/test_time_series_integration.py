"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector import (
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)


class PreWriteIntegrationTestTimeSeriesChecks(TestCase):
    def setUp(self):
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )

    def test_check_regular_timestamps(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
        self.nwbfile.add_acquisition(time_series)
        self.assertEqual(
            first=check_regular_timestamps(
                time_series=self.nwbfile.acquisition["test_time_series"]
            ),
            second=(
                "TimeSeries appears to have a constant sampling rate. "
                f"Consider specifying starting_time={time_series.timestamps[0]} "
                f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
            ),
        )

    def test_check_data_orientation(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=(2, 100)),
                rate=1.0,
            )
        )
        self.assertEqual(
            first=check_data_orientation(
                time_series=self.nwbfile.acquisition["test_time_series"]
            ),
            second=(
                "Data orientation may be in the wrong orientation. "
                "Time should be in the first dimension, and is usually the longest dimension. "
                "Here, another dimension is longer. "
            ),
        )

    def test_check_timestamps_match_first_dimension_1d(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=4),
                timestamps=[1.0, 2.0, 3.0],
            )
        )
        self.assertEqual(
            first=check_timestamps_match_first_dimension(
                time_series=self.nwbfile.acquisition["test_time_series"]
            ),
            second="The length of the first dimension of data does not match the length of timestamps.",
        )

    def test_check_timestamps_match_first_dimension_2d(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=(2, 3)),
                timestamps=[1.0, 2.0, 3.0],
            )
        )
        self.assertEqual(
            first=check_timestamps_match_first_dimension(
                time_series=self.nwbfile.acquisition["test_time_series"]
            ),
            second="The length of the first dimension of data does not match the length of timestamps.",
        )


class PostWriteIntegrationTestTimeSeriesChecks(TestCase):
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

    def assertPostWriteCheck(self, check_function, true_message: str):
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            self.assertEqual(
                first=check_function(
                    time_series=written_nwbfile.acquisition["test_time_series"]
                ),
                second=true_message,
            )

    def test_check_regular_timestamps(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
        self.nwbfile.add_acquisition(time_series)
        self.assertPostWriteCheck(
            check_function=check_regular_timestamps,
            true_message=(
                "TimeSeries appears to have a constant sampling rate. "
                f"Consider specifying starting_time={time_series.timestamps[0]} "
                f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
            ),
        )

    def test_check_data_orientation(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=(2, 100)),
                rate=1.0,
            )
        )
        self.assertPostWriteCheck(
            check_function=check_data_orientation,
            true_message=(
                "Data orientation may be in the wrong orientation. "
                "Time should be in the first dimension, and is usually the longest dimension. "
                "Here, another dimension is longer. "
            ),
        )

    def test_check_timestamps_match_first_dimension_1d(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=4),
                timestamps=[1.0, 2.0, 3.0],
            )
        )
        self.assertPostWriteCheck(
            check_function=check_timestamps_match_first_dimension,
            true_message="The length of the first dimension of data does not match the length of timestamps.",
        )

    def test_check_timestamps_match_first_dimension_2d(self):
        self.nwbfile.add_acquisition(
            pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.zeros(shape=(2, 3)),
                timestamps=[1.0, 2.0, 3.0],
            )
        )
        self.assertPostWriteCheck(
            check_function=check_timestamps_match_first_dimension,
            true_message="The length of the first dimension of data does not match the length of timestamps.",
        )
