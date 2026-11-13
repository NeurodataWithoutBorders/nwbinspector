"""Check functions that can apply to any descendant of TimeSeries."""

from typing import Iterable, Optional

import numpy as np
from pynwb import NWBFile, TimeSeries
from pynwb.ecephys import SpikeEventSeries
from pynwb.epoch import TimeIntervals
from pynwb.image import ImageSeries, IndexSeries

from .._registration import Importance, InspectorMessage, Severity, register_check
from ..utils import get_data_shape, is_ascending_series, is_regular_series


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_regular_timestamps(
    time_series: TimeSeries, time_tolerance_decimals: int = 9, gb_severity_threshold: float = 1.0
) -> Optional[InspectorMessage]:
    """If the TimeSeries uses timestamps, check if they are regular (i.e., they have a constant rate)."""
    if (
        time_series.timestamps is not None
        and len(time_series.timestamps) > 2
        and is_regular_series(series=time_series.timestamps, tolerance_decimals=time_tolerance_decimals)
        and (time_series.timestamps[1] - time_series.timestamps[0]) != 0
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
                f"and rate={1 / (time_series.timestamps[1] - time_series.timestamps[0])} instead of timestamps."
            ),
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_data_orientation(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """If the TimeSeries has data, check if the longest axis (almost always time) is also the zero-axis."""

    # Skip this check for SpikeEventSeries since its data structure is (events, channels, waveform samples)
    # and it's valid for the number of waveform samples to be larger than the number of events
    if isinstance(time_series, SpikeEventSeries):
        return None

    if time_series.data is None:
        return None

    data_shape = get_data_shape(time_series.data)
    if data_shape is None:
        return None

    if any(np.array(data_shape[1:]) > data_shape[0]):
        longest_axis = int(np.argmax(data_shape))
        return InspectorMessage(
            message=(
                f"Data may be in the wrong orientation. "
                f"Time should be in the first dimension, and is usually the longest dimension. "
                f"Here, another dimension is longer. "
                f"Current shape: {data_shape}. "
                f"Suggestion: Transpose your data so the first dimension is {data_shape[longest_axis]}."
            ),
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_timestamps_match_first_dimension(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """
    If the TimeSeries has timestamps, check if their length is the same as the zero-axis of data.

    Best Practice: :ref:`best_practice_data_orientation`
    """
    if time_series.data is None or time_series.timestamps is None:
        return None

    data_shape = get_data_shape(time_series.data)
    if data_shape is None:
        return None

    timestamps_shape = get_data_shape(time_series.timestamps)
    if timestamps_shape is None:
        return None

    if getattr(time_series, "external_file", None) is not None and data_shape[0] == 0:
        return None

    # A very specific edge case where this has been allowed, though much more preferable
    # to use a stack of Images rather than an ImageSeries
    if (
        isinstance(time_series, ImageSeries)
        and len(time_series.timestamps) == 0
        and time_series.get_ancestor("NWBFile") is not None
    ):
        for neurodata_object in time_series.get_ancestor("NWBFile").objects.values():
            if isinstance(neurodata_object, IndexSeries) and neurodata_object.indexed_timeseries == time_series:
                return None

    if data_shape[0] != timestamps_shape[0]:
        return InspectorMessage(
            message=(
                f"The length of the first dimension of data ({data_shape[0]}) "
                f"does not match the length of timestamps ({timestamps_shape[0]})."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_timestamps_ascending(time_series: TimeSeries, nelems: Optional[int] = 200) -> Optional[InspectorMessage]:
    """Check that the values in the timestamps array are strictly increasing."""
    if time_series.timestamps is not None and not is_ascending_series(time_series.timestamps, nelems=nelems):
        return InspectorMessage(f"{time_series.name} timestamps are not ascending.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_timestamps_without_nans(time_series: TimeSeries, nelems: Optional[int] = 200) -> Optional[InspectorMessage]:
    """Check if there are NaN values in the timestamps array."""
    if time_series.timestamps is not None and np.isnan(time_series.timestamps[:nelems]).any():
        return InspectorMessage(message=f"{time_series.name} timestamps contain NaN values.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=TimeSeries)
def check_timestamp_of_the_first_sample_is_not_negative(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """
    Check that the timestamp of the first sample is not negative.

    Best Practice: :ref:`best_practice_avoid_negative_timestamps`
    """
    if time_series.starting_time is not None:
        first_timestamp = time_series.starting_time
    elif time_series.timestamps is not None and len(time_series.timestamps) > 0:
        first_timestamp = time_series.timestamps[0]
    else:
        return None

    if first_timestamp < 0:
        message = (
            "Timestamps should not be negative. This usually indicates a temporal misalignment of the data. "
            "It is recommended to align the `session_start_time` or `timestamps_reference_time` to be the earliest time value that occurs in the data, and shift all other signals accordingly."
        )
        return InspectorMessage(message=message)

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_missing_unit(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """
    Check if the TimeSeries.unit field is empty.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if not time_series.unit:
        return InspectorMessage(
            message="Missing text for attribute 'unit'. Please specify the scientific unit of the 'data'."
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_resolution(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """Check the resolution value of a TimeSeries for proper format (-1.0 or NaN for unknown)."""
    if time_series.resolution is None or time_series.resolution == -1.0:
        return None
    if time_series.resolution <= 0:
        return InspectorMessage(
            message=f"'resolution' should use -1.0 or NaN for unknown instead of {time_series.resolution}."
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_rate_is_not_zero(time_series: TimeSeries) -> Optional[InspectorMessage]:
    if time_series.data is None:
        return None

    data_shape = get_data_shape(time_series.data)
    if data_shape is None:
        return None

    if time_series.rate == 0.0 and data_shape[0] > 1:
        return InspectorMessage(
            f"{time_series.name} has a sampling rate value of 0.0Hz but the series has more than one frame."
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_rate_is_positive(time_series: TimeSeries) -> Optional[InspectorMessage]:
    if not hasattr(time_series, "rate"):
        return None

    if time_series.rate is not None and time_series.rate < 0.0:
        return InspectorMessage(
            message=f"{time_series.name} has a negative sampling rate value of {time_series.rate}Hz which is not valid."
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_time_series_duration(
    time_series: TimeSeries, duration_threshold: float = 31557600.0
) -> Optional[InspectorMessage]:
    """
    Check if the TimeSeries duration is longer than the specified threshold.

    The default threshold is 1 year (31,557,600 seconds = 365.25 days).
    Duration is calculated from either timestamps or starting_time + rate + data length.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if time_series.data is None:
        return None

    data_shape = get_data_shape(time_series.data)
    if data_shape is None or data_shape[0] <= 1:
        return None

    duration = None

    # Calculate duration from timestamps if available
    if time_series.timestamps is not None:
        timestamps_shape = get_data_shape(time_series.timestamps)
        if timestamps_shape is not None and timestamps_shape[0] > 1:
            first_timestamp = time_series.timestamps[0]
            last_timestamp = time_series.timestamps[-1]
            duration = float(last_timestamp - first_timestamp)

    # Calculate duration from starting_time and rate if timestamps not available
    elif time_series.rate is not None and time_series.rate > 0:
        num_samples = data_shape[0]
        duration = (num_samples - 1) / time_series.rate

    # If we have a duration, check if it exceeds the threshold
    if duration is not None and duration > duration_threshold:
        # Convert duration to years for the message
        duration_years = duration / 31557600.0
        return InspectorMessage(
            message=(
                f"TimeSeries '{time_series.name}' has an unusually long duration of {duration:.2f} seconds ({duration_years:.2f} years), "
                f"which may indicate an error in the timestamps or rate data. "
                "Please verify that this is correct."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_time_series_data_is_not_empty(time_series: TimeSeries) -> Optional[InspectorMessage]:
    """
    Check if a TimeSeries has empty data.

    Empty datasets are often the result of incomplete data entry or errors during conversion.

    ImageSeries with external_file set intentionally have empty data and are skipped.

    Best Practice: :ref:`best_practice_data_not_empty`
    """
    data = time_series.data

    # ImageSeries (and subclasses) with external_file intentionally have empty data arrays
    is_image_series_with_external_file = (
        getattr(time_series, "external_file", None) is not None and len(time_series.external_file) > 0
    )
    if is_image_series_with_external_file:
        return None

    # .size works for numpy arrays, h5py.Dataset, zarr.Array, DataIO(wrapping arrays), and StrDataset
    # len() covers lists, tuples, and DataIO(wrapping lists)
    if hasattr(data, "size"):
        is_empty = data.size == 0
    elif isinstance(data, (list, tuple)):
        is_empty = len(data) == 0
    else:
        return None

    if is_empty:
        return InspectorMessage(
            message=(
                f"The 'data' field of {time_series.name} is empty. "
                "Please verify that data was properly added during conversion."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeSeries)
def check_rate_not_below_threshold(
    time_series: TimeSeries, low_rate_threshold: float = 0.01
) -> Optional[InspectorMessage]:
    """
    Check if the sampling rate is suspiciously low (below threshold, default 0.01 Hz).

    A very low rate likely indicates the period (time between samples) was provided instead of the frequency.
    The default threshold of 0.01 Hz corresponds to a period of 100 seconds.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if not hasattr(time_series, "rate"):
        return None

    if time_series.rate is not None and 0 < time_series.rate < low_rate_threshold:
        period = 1.0 / time_series.rate
        return InspectorMessage(
            message=(
                f"TimeSeries '{time_series.name}' has a sampling rate of {time_series.rate} Hz (one sample every {period:.2f} seconds). "
                "This low value may indicate the sampling period was provided instead of the rate. "
                f"If the sampling period of the data is indeed {time_series.rate} seconds, the rate should be set to {1.0 / time_series.rate} Hz instead."
            )
        )

    return None


def _end_time(neurodata_object: object) -> Optional[float]:
    """The last time of a TimeSeries or of a TimeIntervals table, in seconds, from one or a few small reads."""
    if isinstance(neurodata_object, TimeSeries):
        if neurodata_object.timestamps is not None:
            if len(neurodata_object.timestamps) == 0:
                return None
            return float(neurodata_object.timestamps[-1])
        n_samples = get_data_shape(neurodata_object.data)[0] if neurodata_object.data is not None else 0
        if not n_samples or not neurodata_object.rate:
            return None
        return float(neurodata_object.starting_time or 0.0) + (n_samples - 1) / float(neurodata_object.rate)
    if isinstance(neurodata_object, TimeIntervals) and "stop_time" in neurodata_object.colnames:
        if len(neurodata_object.id) == 0:
            return None
        stop_times = np.asarray(neurodata_object["stop_time"].data[:], dtype=float)
        return float(np.nanmax(stop_times)) if np.isfinite(stop_times).any() else None
    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBFile)
def check_time_extents_agree(
    nwbfile: NWBFile, ratio_threshold: float = 1.5, gap_threshold: float = 60.0
) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that no time series or interval table ends far later than everything else in the file.

    An object whose last time is more than ``ratio_threshold`` times, and more than ``gap_threshold`` seconds, later
    than the latest end of all other objects usually has times in another unit (milliseconds for seconds), a wrong
    rate, samples written twice, or an offset the rest of the file does not share.

    Best Practice: :ref:`best_practice_time_series_global_time_reference`
    """
    ends = []
    for neurodata_object in nwbfile.objects.values():
        end = _end_time(neurodata_object)
        if end is not None and np.isfinite(end) and end > 0:
            ends.append((neurodata_object, end))
    if len(ends) < 2:
        return None
    ordered = sorted(ends, key=lambda item: item[1], reverse=True)
    (latest, latest_end), (next_latest, next_end) = ordered[0], ordered[1]
    if latest_end > ratio_threshold * next_end and latest_end - next_end > gap_threshold:
        yield InspectorMessage(
            message=(
                f"{type(latest).__name__} '{latest.name}' ends at {latest_end:g} s, {latest_end / next_end:.3g} times "
                f"later than everything else in the file (the next latest, {type(next_latest).__name__} "
                f"'{next_latest.name}', ends at {next_end:g} s). Check its times for a unit, rate or offset error."
            )
        )

    return None
