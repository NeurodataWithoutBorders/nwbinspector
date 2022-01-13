"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase

import pynwb

from nwbinspector.check_time_series import (
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)


class UnitTestTimeSeriesChecks(TestCase):
    def test_check_regular_timestamps(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
        self.assertEqual(
            first=check_regular_timestamps(time_series=time_series),
            second=(
                "TimeSeries appears to have a constant sampling rate. "
                f"Consider specifying starting_time={time_series.timestamps[0]} "
                f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
            ),
        )

    def test_check_data_orientation(self):
        self.assertEqual(
            first=check_data_orientation(
                time_series=pynwb.TimeSeries(
                    name="test_time_series",
                    unit="test_units",
                    data=np.zeros(shape=(2, 100)),
                    rate=1.0,
                )
            ),
            second=(
                "Data orientation may be in the wrong orientation. "
                "Time should be in the first dimension, and is usually the longest dimension. "
                "Here, another dimension is longer. "
            ),
        )

    def test_check_timestamps_match_first_dimension_1d(self):
        self.assertEqual(
            first=check_timestamps_match_first_dimension(
                time_series=pynwb.TimeSeries(
                    name="test_time_series",
                    unit="test_units",
                    data=np.zeros(shape=4),
                    timestamps=[1.0, 2.0, 3.0],
                )
            ),
            second="The length of the first dimension of data does not match the length of timestamps.",
        )

    def test_check_timestamps_match_first_dimension_2d(self):
        self.assertEqual(
            first=check_timestamps_match_first_dimension(
                time_series=pynwb.TimeSeries(
                    name="test_time_series",
                    unit="test_units",
                    data=np.zeros(shape=(2, 3)),
                    timestamps=[1.0, 2.0, 3.0],
                )
            ),
            second="The length of the first dimension of data does not match the length of timestamps.",
        )
