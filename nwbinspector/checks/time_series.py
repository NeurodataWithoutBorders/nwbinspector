"""Check functions that can apply to any descendant of TimeSeries."""
import numpy as np

from pynwb import TimeSeries
from pynwb.image import ImageSeries

from ..register_checks import register_check, Importance, Severity, InspectorMessage
from ..utils import check_regular_series, is_ascending_series


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_regular_timestamps(
    time_series: TimeSeries, time_tolerance_decimals: int = 9, gb_severity_threshold: float = 1.0
):
    """If the TimeSeries uses timestamps, check if they are regular (i.e., they have a constant rate)."""
    if time_series.timestamps is not None and check_regular_series(
        series=time_series.timestamps, tolerance_decimals=time_tolerance_decimals
    ):
        timestamps = np.array(time_series.timestamps)
        if timestamps.size * timestamps.dtype.itemsize > gb_severity_threshold * 1e9:
            severity = Severity.HIGH
        else:
            severity = Severity.LOW
        return InspectorMessage(
            severity=severity,
            message=(
                "TimeSeries appears to have a constant sampling rate. "
                f"Consider specifying starting_time={time_series.timestamps[0]} "
                f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
            ),
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_data_orientation(time_series: TimeSeries):
    """If the TimeSeries has data, check if the longest axis (almost always time) is also the zero-axis."""
    if time_series.data is not None and any(np.array(time_series.data.shape[1:]) > time_series.data.shape[0]):
        return InspectorMessage(
            message=(
                "Data may be in the wrong orientation. "
                "Time should be in the first dimension, and is usually the longest dimension. "
                "Here, another dimension is longer."
            ),
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_timestamps_match_first_dimension(time_series: TimeSeries):
    """
    If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data.

    Best Practice: :ref:`best_practice_data_orientation`
    """
    if (
        time_series.data is not None
        and time_series.timestamps is not None
        and np.array(time_series.data).shape[:1] != np.array(time_series.timestamps).shape
    ):
        return InspectorMessage(
            message="The length of the first dimension of data does not match the length of timestamps.",
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_timestamps_ascending(time_series: TimeSeries, nelems=200):
    """Check that the values in the timestamps array are strictly increasing."""
    if time_series.timestamps is not None and not is_ascending_series(time_series.timestamps, nelems=nelems):
        return InspectorMessage(f"{time_series.name} timestamps are not ascending.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_time_series_data_is_not_none(time_series: TimeSeries, nelems: int = 200):
    """Check that the data values in a TimeSeries are not None."""
    if isinstance(time_series, ImageSeries):
        if time_series.external_file is not None:
            return
    if time_series.data is None or any((x is None for x in time_series.data[:nelems])):
        return InspectorMessage("Data values in a TimeSeries cannot be None.")


# TODO: break up logic of extra stuff into separate checks
# def check_timeseries(nwbfile):
#     """Check dataset values in TimeSeries objects"""
#     for ts in all_of_type(nwbfile, pynwb.TimeSeries):
#         if not (np.isnan(ts.resolution) or ts.resolution == -1.0) and ts.resolution <= 0:
#             error_code = "A101"
#             print(
#                 "- %s: '%s' %s data attribute 'resolution' should use -1.0 or NaN for unknown instead of %f"
#                 % (error_code, ts.name, type(ts).__name__, ts.resolution)
#             )
#         if not ts.unit:
#             error_code = "A101"
#             print("- %s: '%s' %s data is missing text for attribute 'unit'"
# % (error_code, ts.name, type(ts).__name__))
