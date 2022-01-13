"""Authors: Cody Baker and Ben Dichter."""
import numpy as np

import pynwb
import h5py

from .utils import add_to_default_checks, check_regular_series


@add_to_default_checks(severity=1, neurodata_type=pynwb.TimeSeries)
def check_dataset_compression(time_series: pynwb.TimeSeries, bytes_threshold=2e6):
    """
    If the data in the TimeSeries object is a h5py.Dataset, check if it has compression enabled.

    Will only run if the size of the h5py.Dataset is larger than bytes_threshold.
    """
    if isinstance(time_series.data, h5py.Dataset):
        if (
            time_series.data.size * time_series.data.dtype.itemsize > bytes_threshold
            and time_series.data.compression is None
        ):
            return "Consider enabling compression when writing a large dataset."


@add_to_default_checks(severity=2, neurodata_type=pynwb.TimeSeries)
def check_regular_timestamps(time_series: pynwb.TimeSeries, time_tol_decimals=9):
    """If the TimeSeries uses timestamps, check if they are regular (i.e., they have a constant rate)."""
    if time_series.timestamps is not None and check_regular_series(
        series=time_series.timestamps, tolerance_decimals=time_tol_decimals
    ):
        return (
            f"The {type(time_series).__name__} '{time_series.name}' has a constant sampling rate. "
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
            f"The {type(time_series).__name__} '{time_series.name}' data orientation appears to be incorrect. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer. "
            "This is possibly correct, but usually indicates that the data is in the wrong orientation."
        )


@add_to_default_checks(severity=3, neurodata_type=pynwb.TimeSeries)
def check_timestamps_match_first_dimension(time_series: pynwb.TimeSeries):
    """If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data."""
    if (
        time_series.data is not None
        and len(time_series.data.shape) > 1
        and time_series.timestamps is not None
        and len(time_series.data) != len(time_series.timestamps)
    ):
        return (
            f"{type(time_series).__name__} {'ts.name'} data orientation appears to be incorrect. "
            "The length of the first dimension of data does not match the length of timestamps."
        )
