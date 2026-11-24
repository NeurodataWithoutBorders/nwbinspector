"""Check functions that can apply to any descendant of TimeSeries."""

import weakref
from typing import Optional

import numpy as np
from pynwb import NWBFile, TimeSeries
from pynwb.ecephys import SpikeEventSeries
from pynwb.image import ImageSeries, IndexSeries

from .._registration import Importance, InspectorMessage, Severity, register_check
from ..utils import _comparison, get_data_shape, is_ascending_series, is_regular_series


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


_identical_series_cache: "weakref.WeakKeyDictionary" = weakref.WeakKeyDictionary()


def _same_h5_object(a: _comparison.DataLike, b: _comparison.DataLike) -> bool:
    """True when two datasets are the same HDF5 object (a link), not two copies."""
    a5, b5 = _comparison.h5_dataset(a), _comparison.h5_dataset(b)
    if a5 is None or b5 is None:
        return a is b
    try:
        return a5.id == b5.id
    except Exception:
        return a5.name == b5.name and a5.file == b5.file


def _fingerprint(data: _comparison.DataLike) -> tuple[str, bool, bool]:
    """Return (digest, exact, constant) of a dataset. exact is False when only sampled blocks were hashed."""
    shape = _comparison.data_shape(data)
    dtype = _comparison.data_dtype(data)
    parts = [repr((shape, str(dtype)))]
    if len(shape) == 0 or int(np.prod(shape, dtype=np.int64)) * dtype.itemsize <= _comparison.FULL_READ_BYTES:
        values = np.asarray(data[()] if len(shape) == 0 else data[:])
        parts.append(_comparison.digest(values))
        return _comparison.digest(np.array(parts)), True, _comparison.is_constant(values)
    constant = True
    first = None
    for selection in _comparison.sample_blocks(data):
        values = np.asarray(data[selection])
        parts.append(_comparison.digest(values))
        if constant:
            if not _comparison.is_constant(values):
                constant = False
            elif first is None:
                first = values.reshape(-1)[:1]
            elif not np.array_equal(first, values.reshape(-1)[:1], equal_nan=values.dtype.kind == "f"):
                constant = False
    return _comparison.digest(np.array(parts)), False, constant


def _object_path(obj: _comparison.DataLike) -> str:
    parts = []
    while obj is not None and not isinstance(obj, NWBFile):
        parts.append(obj.name)
        obj = obj.parent
    return "/".join(reversed(parts))


def _identical_time_series_groups(nwbfile: NWBFile) -> list[dict]:
    """
    Groups of TimeSeries in one file whose data are identical, computed once per file and shared by
    check_identical_time_series and check_redundant_time_series_copies.

    Series are grouped by data shape and dtype, so only series that could match are read, and then by a hash of a
    small block at the start, so only series that agree there are read in full (or on sampled blocks). Pairs whose
    data are the same HDF5 object (a link) are not reported, nor are constant data on a rate-based time base (for
    example two empty or all-zero channels).
    """
    try:
        return _identical_series_cache[nwbfile]
    except (KeyError, TypeError):
        pass
    by_shape: dict[tuple, list] = {}
    for obj in nwbfile.objects.values():
        if not isinstance(obj, TimeSeries) or obj.data is None or isinstance(obj.data, TimeSeries):
            continue
        try:
            shape = _comparison.data_shape(obj.data)
        except Exception:
            continue
        if len(shape) == 0 or shape[0] < 2:
            continue
        by_shape.setdefault((shape, str(_comparison.data_dtype(obj.data))), []).append(obj)

    found = []
    for series in by_shape.values():
        if len(series) < 2:
            continue
        by_head: dict[str, list] = {}
        for time_series in series:
            head = _comparison.sample_blocks(time_series.data, block_bytes=64 * 1024, n_blocks=1)[0]
            by_head.setdefault(_comparison.digest(np.asarray(time_series.data[head])), []).append(time_series)
        by_fingerprint: dict[str, list] = {}
        info = {}
        for head_group in by_head.values():
            if len(head_group) < 2:
                continue
            for time_series in head_group:
                fingerprint, exact, constant = _fingerprint(time_series.data)
                info[id(time_series)] = (exact, constant)
                by_fingerprint.setdefault(fingerprint, []).append(time_series)
        for same in by_fingerprint.values():
            distinct: list[TimeSeries] = []  # drop members that are links to an earlier member's data
            for time_series in same:
                if not any(_same_h5_object(time_series.data, other.data) for other in distinct):
                    distinct.append(time_series)
            if len(distinct) < 2:
                continue
            constant = info[id(distinct[0])][1]

            def time_base(time_series: TimeSeries) -> tuple:
                if time_series.timestamps is not None:
                    return ("timestamps", _fingerprint(time_series.timestamps)[0])
                return ("rate", time_series.starting_time, time_series.rate)

            if constant:
                # Constant data (all ones, all zeros) only count as a duplicate when the series also carry the
                # same explicit timestamps, stored separately rather than linked.
                by_time_base: dict[tuple, list] = {}
                for time_series in distinct:
                    base = time_base(time_series)
                    if base[0] == "timestamps":
                        by_time_base.setdefault(base, []).append(time_series)
                subgroups = [
                    (group, True)
                    for group in by_time_base.values()
                    if len(group) > 1
                    and not all(_same_h5_object(group[0].timestamps, other.timestamps) for other in group[1:])
                ]
            else:
                subgroups = [(distinct, len({time_base(t) for t in distinct}) == 1)]
            for group, same_time in subgroups:
                # A copy is most likely wrong data when the series are of different kinds: an event series
                # (constant values at explicit times) under two names, different neurodata types or units, or a
                # processed series identical to raw acquisition, which the processing should have changed.
                in_acquisition = {nwbfile.acquisition.get(t.name) is t for t in group}
                wrong = (
                    constant
                    or len({type(t) for t in group}) > 1
                    or len({getattr(t, "unit", None) for t in group}) > 1
                    or len(in_acquisition) > 1
                )
                exact = all(info[id(t)][0] for t in group)
                found.append(dict(group=group, exact=exact, constant=constant, same_time=same_time, wrong=wrong))
    try:
        _identical_series_cache[nwbfile] = found
    except TypeError:
        pass
    return found


def _identical_series_message(found: dict, advice: str) -> InspectorMessage:
    group = found["group"]
    how = "identical" if found["exact"] else f"identical on {_comparison.N_BLOCKS} sampled blocks of"
    time_base = "and the same time base" if found["same_time"] else "but different time bases (timestamps or rate)"
    constant = " The data are constant and the timestamps are identical." if found["constant"] else ""
    return InspectorMessage(
        message=(
            f"{len(group)} TimeSeries hold {how} data of shape {_comparison.data_shape(group[0].data)} {time_base}: "
            f"{', '.join(_object_path(t) for t in group)}.{constant} {advice}"
        )
    )


@register_check(importance=Importance.CRITICAL, neurodata_type=NWBFile)
def check_identical_time_series(nwbfile: NWBFile) -> Optional[list[InspectorMessage]]:
    """
    Two TimeSeries of different kinds should not hold identical data.

    Reported here are identical series that are of different neurodata types or units, a processed series identical
    to a series in acquisition, and event-like series (constant values) that share explicit timestamps under
    different names. In each case one series most likely holds the wrong data. Identical series of the same kind
    are reported by check_redundant_time_series_copies instead.

    Best Practice: :ref:`best_practice_no_identical_series`
    """
    messages = [
        _identical_series_message(
            found, "One of them most likely holds the wrong data; if it is meant to be a copy, link it instead."
        )
        for found in _identical_time_series_groups(nwbfile)
        if found["wrong"]
    ]
    return messages or None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBFile)
def check_redundant_time_series_copies(nwbfile: NWBFile) -> Optional[list[InspectorMessage]]:
    """
    Two TimeSeries of the same kind should not store the same data twice; store it once and link the second
    series to it. Check that both are meant to hold the same data.

    Best Practice: :ref:`best_practice_no_identical_series`
    """
    messages = [
        _identical_series_message(
            found,
            "If both are meant to hold the same data, store it once and link the other series to it; "
            "otherwise one of them holds the wrong data.",
        )
        for found in _identical_time_series_groups(nwbfile)
        if not found["wrong"]
    ]
    return messages or None


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
