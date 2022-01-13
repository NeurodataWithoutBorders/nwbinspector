"""Authors: Cody Baker and Ben Dichter."""
import numpy as np

import pynwb

from ..utils import add_to_default_checks, check_regular_series


@add_to_default_checks(severity=2, neurodata_type=pynwb.TimeSeries)
def check_regular_timestamps(time_series: pynwb.TimeSeries, time_tol_decimals=9):
    """If the TimeSeries uses timestamps, check if they are regular (i.e., they have a constant rate)."""
    if time_series.timestamps is not None and check_regular_series(
        series=time_series.timestamps, tolerance_decimals=time_tol_decimals
    ):
        return (
            "TimeSeries appears to have a constant sampling rate. "
            f"Consider specifying starting_time={time_series.timestamps[0]} "
            f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
        )


@add_to_default_checks(severity=2, neurodata_type=pynwb.TimeSeries)
def check_data_orientation(time_series: pynwb.TimeSeries):
    """If the TimeSeries has data, check if the longest axis (almost always time) is also the zero-axis."""
    if time_series.data is not None and any(
        np.array(time_series.data.shape[1:]) > time_series.data.shape[0]
    ):
        return (
            "Data orientation may be in the wrong orientation. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer. "
        )


@add_to_default_checks(severity=3, neurodata_type=pynwb.TimeSeries)
def check_timestamps_match_first_dimension(time_series: pynwb.TimeSeries):
    """If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data."""
    if (
        time_series.data is not None
        and time_series.timestamps is not None
        and time_series.data.shape[0] != len(time_series.timestamps)
    ):
        return "The length of the first dimension of data does not match the length of timestamps."
