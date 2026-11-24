"""Check functions that can apply to any descendant of TimeSeries."""

from typing import Optional

import numpy as np
from pynwb import TimeSeries
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


# Most uncompressed chunk data that the sampled column comparison of one series may decompress.
MAX_COLUMN_FETCH_BYTES = 64 * 1024**2
# Most columns a 2-D TimeSeries may have for the column comparison.
MAX_COMPARED_COLUMNS = 1024


def _fetch_bytes(data: _comparison.DataLike, rows: slice, columns: Optional[list] = None) -> int:
    """
    Uncompressed bytes that reading data[rows, columns] of a 2-D dataset decompresses. HDF5 reads whole chunks,
    so a few rows of a dataset chunked as (1048576, 16) cost far more than their size.
    """
    shape = _comparison.data_shape(data)
    itemsize = _comparison.data_dtype(data).itemsize
    columns = list(range(shape[1])) if columns is None else columns
    dataset = _comparison.h5_dataset(data)
    if dataset is None or not dataset.chunks:
        return (rows.stop - rows.start) * len(columns) * itemsize
    chunk_rows, chunk_columns = dataset.chunks[0], dataset.chunks[1]
    n_row_chunks = (min(rows.stop, shape[0]) - 1) // chunk_rows - rows.start // chunk_rows + 1
    n_column_chunks = len({column // chunk_columns for column in columns})
    return n_row_chunks * n_column_chunks * chunk_rows * chunk_columns * itemsize


def _row_blocks(data: _comparison.DataLike) -> list[slice]:
    """
    Row slices that sample a 2-D dataset at N_BLOCKS places, each of at most about BLOCK_BYTES and each inside a
    single chunk row, so that a block decompresses one row of chunks and not two.
    """
    n_rows, n_columns = _comparison.data_shape(data)[:2]
    itemsize = _comparison.data_dtype(data).itemsize
    size = max(1, min(n_rows, _comparison.BLOCK_BYTES // max(1, n_columns * itemsize)))
    dataset = _comparison.h5_dataset(data)
    chunk_rows = dataset.chunks[0] if dataset is not None and dataset.chunks else None
    if chunk_rows:
        size = min(size, chunk_rows)
    blocks: list[slice] = []
    for start in np.linspace(0, max(0, n_rows - size), _comparison.N_BLOCKS).astype(int).tolist():
        if chunk_rows:
            start = min((start // chunk_rows) * chunk_rows, n_rows - size)
        if not blocks or start != blocks[-1].start:
            blocks.append(slice(start, start + size))
    return blocks


def _read_columns(data: _comparison.DataLike, rows: slice, columns: list) -> np.ndarray:
    if _comparison.h5_dataset(data) is not None:
        return np.asarray(data[rows, columns])
    low, high = min(columns), max(columns) + 1
    return np.asarray(data[rows, low:high])[:, [column - low for column in columns]]


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeSeries)
def check_time_series_identical_columns(
    time_series: TimeSeries, max_fetch_bytes: int = MAX_COLUMN_FETCH_BYTES
) -> Optional[InspectorMessage]:
    """
    Two columns (channels or dimensions) of a 2-D TimeSeries should not be identical, for example the z coordinate
    of a position that copies y.

    Small series are compared whole. Large series are compared in two stages: every column on a first block of
    rows, then only the columns that match there on further blocks. Blocks are aligned to the HDF5 chunk rows, and
    a series whose first block alone would decompress more than max_fetch_bytes of chunks is skipped, since reading
    it remotely is slow.

    Best Practice: :ref:`best_practice_no_identical_time_series_columns`
    """
    data = time_series.data
    if data is None or isinstance(data, TimeSeries):
        return None
    try:
        shape = _comparison.data_shape(data)
    except Exception:
        return None
    if len(shape) != 2 or not 2 <= shape[1] <= MAX_COMPARED_COLUMNS or shape[0] < _comparison.MIN_DISTINCT_FOR_COLUMNS:
        return None
    if _comparison.data_dtype(data).kind not in "fiub":
        return None

    def nontrivial(column: np.ndarray) -> bool:
        finite = column[~np.isnan(column)] if column.dtype.kind == "f" else column
        return len(np.unique(finite)) >= _comparison.MIN_DISTINCT_FOR_COLUMNS

    keys: dict[int, tuple[str, ...]]
    exact = shape[0] * shape[1] * _comparison.data_dtype(data).itemsize <= _comparison.FULL_READ_BYTES
    if exact:
        values = np.asarray(data[:])
        keys = {j: (_comparison.digest(values[:, j]),) for j in range(shape[1]) if nontrivial(values[:, j])}
        n_blocks = 0
    else:
        blocks = _row_blocks(data)
        budget = max_fetch_bytes - _fetch_bytes(data, blocks[0])
        if budget < 0:
            return None
        head = np.asarray(data[blocks[0]])
        keys = {j: (_comparison.digest(head[:, j]),) for j in range(shape[1]) if nontrivial(head[:, j])}
        n_blocks = 1
        for rows in blocks[1:]:
            counts: dict[tuple, int] = {}
            for key in keys.values():
                counts[key] = counts.get(key, 0) + 1
            candidates = sorted(j for j, key in keys.items() if counts[key] > 1)
            if not candidates:
                break
            cost = _fetch_bytes(data, rows, candidates)
            if cost > budget:
                break
            budget -= cost
            block = _read_columns(data, rows, candidates)
            keys = {j: keys[j] + (_comparison.digest(block[:, i]),) for i, j in enumerate(candidates)}
            n_blocks += 1

    by_key: dict[tuple, list] = {}
    for j, key in keys.items():
        by_key.setdefault(key, []).append(j)
    groups = [group for group in by_key.values() if len(group) > 1]
    if not groups:
        return None
    where = "in every row" if exact else f"on {n_blocks} sampled block(s) of rows"
    examples = _comparison.format_examples(["columns " + " = ".join(map(str, group)) for group in groups])
    return InspectorMessage(message=f"{len(groups)} group(s) of columns of the data are identical {where}: {examples}.")


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
