"""Authors: Cody Baker, Ben Dichter, and Ryan Ly."""
import numpy as np

import pynwb

from ..tools import all_of_type
from ..utils import nwbinspector_check, check_regular_series


@nwbinspector_check(severity=2, neurodata_type=pynwb.TimeSeries)
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


@nwbinspector_check(severity=2, neurodata_type=pynwb.TimeSeries)
def check_data_orientation(time_series: pynwb.TimeSeries):
    """If the TimeSeries has data, check if the longest axis (almost always time) is also the zero-axis."""
    if time_series.data is not None and any(np.array(time_series.data.shape[1:]) > time_series.data.shape[0]):
        return (
            "Data orientation may be in the wrong orientation. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer. "
        )


@nwbinspector_check(severity=3, neurodata_type=pynwb.TimeSeries)
def check_timestamps_match_first_dimension(time_series: pynwb.TimeSeries):
    """If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data."""
    if (
        time_series.data is not None
        and time_series.timestamps is not None
        and time_series.data.shape[0] != len(time_series.timestamps)
    ):
        return "The length of the first dimension of data does not match the length of timestamps."


# TODO: break up logic of extra stuff into separate checks
def check_timeseries(nwbfile):
    """Check dataset values in TimeSeries objects"""
    for ts in all_of_type(nwbfile, pynwb.TimeSeries):
        if ts.data is None:
            # exception to the rule: ImageSeries objects are allowed to have no data
            if not isinstance(ts, pynwb.image.ImageSeries):
                error_code = "A101"
                print("- %s: '%s' %s data is None" % (error_code, ts.name, type(ts).__name__))
            else:
                if ts.external_file is None:
                    error_code = "A101"
                    print(
                        "- %s: '%s' %s data is None and external_file is None"
                        % (error_code, ts.name, type(ts).__name__)
                    )
            continue

        if not (np.isnan(ts.resolution) or ts.resolution == -1.0) and ts.resolution <= 0:
            error_code = "A101"
            print(
                "- %s: '%s' %s data attribute 'resolution' should use -1.0 or NaN for unknown instead of %f"
                % (error_code, ts.name, type(ts).__name__, ts.resolution)
            )

        if not ts.unit:
            error_code = "A101"
            print("- %s: '%s' %s data is missing text for attribute 'unit'" % (error_code, ts.name, type(ts).__name__))
