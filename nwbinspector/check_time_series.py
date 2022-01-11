"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import numpy as np

from .utils import add_to_default_checks


@add_to_default_checks(severity=2)
def check_regular_timestamps(ts: pynwb.TimeSeries, time_tol_decimals=9):
    if ts.timestamps:
        uniq_diff_ts = np.unique(
            np.diff(ts.timestamps).round(decimals=time_tol_decimals)
        )
        if len(uniq_diff_ts) == 1:
            return (
                "constant sampling rate. Consider using starting_time "
                f"{ts.timestamps[0]} and rate {uniq_diff_ts[0]} instead of using the timestamps array."
            )


@add_to_default_checks(severity=3)
def check_data_orientation(ts: pynwb.TimeSeries):

    if ts.data is not None and len(ts.data.shape) > 1:
        if ts.timestamps is not None:
            if not (len(ts.data) == len(ts.timestamps)):
                return (
                    f"{type(ts).__name__} {'ts.name'} data orientation appears to be incorrect. The length of the "
                    "first dimension of data does not match the length of timestamps."
                )
        else:
            if any(ts.data.shape[1:] > ts.data.shape[0]):
                return (
                    f"{type(ts).__name__} '{ts.name}' data orientation appears to be incorrect. Time should be in "
                    "the first dimension, and is usually the longest dimension. Here, another dimension is longer. "
                    "This is possibly correct, but usually indicates that the data is in the wrong orientation."
                )
