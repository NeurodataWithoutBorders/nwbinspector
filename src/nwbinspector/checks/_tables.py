"""Check functions that can apply to any descendant of DynamicTable."""

from collections import Counter
from numbers import Real
from typing import Iterable, Optional

import numpy as np
from hdmf.common import DynamicTable, DynamicTableRegion, MeaningsTable, VectorIndex
from pynwb.file import TimeIntervals, Units

from .._registration import Importance, InspectorMessage, register_check
from ..utils import (
    cache_data_selection,
    format_byte_size,
    get_data_shape,
    is_ascending_series,
    is_dict_in_string,
    is_string_json_loadable,
)
from ..utils._ordering import plan_windows, scan_ascending

NELEMS = 200
MAX_DURATION = 3600 * 24 * 365.25  # default: 1 year


@register_check(importance=Importance.CRITICAL, neurodata_type=DynamicTableRegion)
def check_dynamic_table_region_data_validity(
    dynamic_table_region: DynamicTableRegion, nelems: Optional[int] = NELEMS
) -> Optional[InspectorMessage]:
    """Check if a DynamicTableRegion is valid."""
    if np.any(np.asarray(dynamic_table_region.data[:nelems]) >= len(dynamic_table_region.table)):
        return InspectorMessage(
            message=(
                f"Some elements of {dynamic_table_region.name} are out of range because they are greater than or "
                "equal to the length of the target table. Note that data should contain indices, not ids."
            )
        )
    if np.any(np.asarray(dynamic_table_region.data[:nelems]) < 0):
        return InspectorMessage(
            message=f"Some elements of {dynamic_table_region.name} are out of range because they are less than 0."
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_empty_table(table: DynamicTable) -> Optional[InspectorMessage]:
    """Check if a DynamicTable is empty."""
    if len(table.id) == 0:
        return InspectorMessage(message="This table has no data added to it.")

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=VectorIndex)
def check_vector_index_data_validity(
    vector_index: VectorIndex, max_bytes: Optional[int] = None
) -> Optional[InspectorMessage]:
    """
    Check that a VectorIndex is a valid set of end offsets into its target.

    The values of a VectorIndex are the end offset of each row in the target array, so they must be
    non-negative and non-decreasing, and the last value must equal the length of the target. When any
    of these fails, readers silently give rows the wrong elements (for example, the spikes of another unit).
    Indexes hold one value per row, so this check is cheap.

    Best Practice: :ref:`best_practice_vector_index_data_validity`
    """
    index_data = vector_index.data
    if isinstance(index_data, (list, tuple)):
        index_data = np.asarray(index_data)
    n_rows = len(index_data)
    target = vector_index.target
    if n_rows == 0 or target is None or getattr(target, "data", None) is None:
        return None
    target_length = len(target.data)
    target_name = target.name
    problems = []

    scan = scan_ascending(data=index_data, ignore_nan=False, max_bytes=max_bytes)
    row = scan.first_descending_position
    if scan.n_descending and row is not None:
        values = np.asarray(index_data[row - 1 : row + 1]).astype(np.int64)
        problems.append(
            f"its values decrease {scan.n_descending:,} time{'s' if scan.n_descending > 1 else ''}, "
            f"first at row {row:,} (from {values[0]:,} to {values[1]:,})"
        )

    first_value = int(np.asarray(index_data[0:1])[0])
    last_value = int(np.asarray(index_data[n_rows - 1 : n_rows])[0])
    if first_value < 0:
        problems.append(f"its first value is negative ({first_value:,})")
    if last_value < target_length:
        problems.append(
            f"its last value is {last_value:,} but '{target_name}' has {target_length:,} elements, "
            f"so the last {target_length - last_value:,} elements belong to no row"
        )
    elif last_value > target_length:
        problems.append(
            f"its last value is {last_value:,} but '{target_name}' has only {target_length:,} elements, "
            "so the last row reads past the end of the data"
        )

    if not problems:
        return None

    message = (
        f"The index '{vector_index.name}' is not a valid set of end offsets into '{target_name}': "
        + "; ".join(problems)
        + ". The values of an index must be non-decreasing and end at the length of the data it indexes, "
        "otherwise rows are given the wrong elements."
    )
    stored_max = np.iinfo(index_data.dtype).max if np.issubdtype(index_data.dtype, np.integer) else None
    if stored_max is not None and stored_max < target_length:
        message += f" The index is stored as {index_data.dtype}, which cannot hold offsets up to {target_length:,}."
    elif target_length >= 2**16 and (scan.n_descending or (target_length - last_value) % 2**16 == 0):
        message += " The offsets may have wrapped at 65,536 (a 16-bit integer overflow) when the file was written."
    if last_value < target_length and first_value == 0 and n_rows > 1:
        message += (
            " The first value is 0, so the index may hold the start offset of each row instead of the end offset, "
            "which gives every row the elements of the row before it."
        )
    return InspectorMessage(message=message)


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeIntervals)
def check_time_intervals_start_time_not_constant(
    time_intervals: TimeIntervals, nelems: Optional[int] = NELEMS
) -> Optional[InspectorMessage]:
    """
    Check if all start_time values are identical.

    Best Practice: :ref:`best_practice_time_interval_time_columns`

    Parameters
    ----------
    time_intervals: TimeIntervals
    nelems: int, optional
        Only check the first {nelems} elements. This is useful in case there columns are
        very long so you don't need to load the entire array into memory. Use None to
        load the entire arrays.
    """
    if len(time_intervals.id) <= 1:
        return None

    start_times = np.asarray(cache_data_selection(data=time_intervals["start_time"].data, selection=slice(nelems)))
    if np.all(start_times == start_times[0]):
        return InspectorMessage(
            message=(
                f"All start_time values are the same value {start_times[0]}. "
                "start_times should be in non-decreasing order and should be "
                "with respect to the session start time."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_interval_time_columns(
    time_intervals: TimeIntervals, nelems: Optional[int] = None, max_bytes: Optional[int] = None
) -> Optional[InspectorMessage]:
    """
    Check that start_time values are in non-decreasing order.

    Despite the function name suggesting multiple time columns, this only checks ``start_time``.
    It was originally written to check all columns ending in ``_time``, but was narrowed in
    PR #382 (see issue #375) because other time columns are not required to be ascending
    across rows. For example, a ``SleepStates`` table may contain overlapping state
    annotations where multiple states (e.g. WAKEtheta, QWake, WAKEnontheta) start at the
    same time with different stop times, making ``stop_time`` non-ascending by design.

    Best Practice: :ref:`best_practice_time_interval_time_columns`

    Parameters
    ----------
    time_intervals: TimeIntervals
    nelems: int, optional
        Only check the first {nelems} elements. The default, None, checks the whole column in chunks.
    max_bytes : int, optional
        Read budget for the column; longer columns are checked on a sample of chunks.
    """
    unsorted_cols = []
    for column in time_intervals.columns:
        if column.name == "start_time":
            if nelems is not None:
                is_sorted = is_ascending_series(column.data, nelems)
            else:
                is_sorted = scan_ascending(data=column.data, ignore_nan=True, max_bytes=max_bytes).n_descending == 0
            if not is_sorted:
                unsorted_cols.append(column.name)
    if unsorted_cols:
        return InspectorMessage(
            message=(
                f"{unsorted_cols} are time columns but the values are not in ascending order. "
                "All times should be in seconds with respect to the session start time."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_intervals_stop_after_start(
    time_intervals: TimeIntervals, nelems: Optional[int] = None, max_bytes: Optional[int] = None
) -> Optional[InspectorMessage]:
    """
    Check that all stop times on a TimeInterval object occur after their corresponding start times.

    Best Practice: :ref:`best_practice_time_interval_time_columns`

    Parameters
    ----------
    time_intervals: TimeIntervals
    nelems: int, optional
        Only check the first {nelems} elements. The default, None, checks every row in chunks.
    max_bytes : int, optional
        Read budget for each column; longer columns are checked on a sample of chunks.
    """
    start_data = time_intervals["start_time"].data
    stop_data = time_intervals["stop_time"].data
    n_rows = min(len(start_data), len(stop_data))
    if nelems is not None:
        n_rows = min(n_rows, nelems)
        windows, sampled = [(0, n_rows)], False
    else:
        windows, sampled = plan_windows(data=start_data, max_bytes=max_bytes)

    n_bad = 0
    first_bad_row = None
    for window_start, window_stop in windows:
        window_stop = min(window_stop, n_rows)
        if window_stop <= window_start:
            continue
        durations = np.asarray(stop_data[window_start:window_stop]) - np.asarray(start_data[window_start:window_stop])
        bad = np.flatnonzero(durations <= 0)
        n_bad += len(bad)
        if first_bad_row is None and len(bad):
            first_bad_row = window_start + int(bad[0])

    if n_bad:
        return InspectorMessage(
            message=(
                "stop_times should be greater than start_times. Make sure the stop times are with respect to the "
                f"session start time. {n_bad:,} row{'s' if n_bad > 1 else ''}"
                f"{' in the sampled chunks' if sampled else ''} ha{'ve' if n_bad > 1 else 's'} a stop_time at or "
                f"before its start_time, first at row {first_bad_row:,}."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_column_binary_capability(
    table: DynamicTable, nelems: Optional[int] = NELEMS
) -> Optional[Iterable[InspectorMessage]]:
    """
    Check each column of a table to see if the data could be set as a boolean dtype.

    Parameters
    ----------
    table: DynamicTable
    nelems: int, optional
        Only check the first {nelems} elements. This is useful in case there columns are
        very long so you don't need to load the entire array into memory. Use None to
        load the entire arrays.
    """
    if len(table.id) == 0:
        return None  # an empty table is reported by check_empty_table

    pre_defined_column_names = [column["name"] for column in getattr(table, "__columns__", list())]
    for column in table.columns:
        if column.name in pre_defined_column_names:
            continue  # The column name and data type cannot be changed by the user
        if hasattr(column, "data") and not isinstance(column, VectorIndex):
            if np.asarray(column.data[0]).itemsize == 1:
                continue  # already boolean, int8, or uint8
            try:
                unique_values = np.unique(cache_data_selection(data=column.data, selection=slice(nelems)))
            except TypeError:  # some contained objects are unhashable or have no comparison defined
                continue
            if unique_values.size != 2:
                continue
            parsed_unique_values = np.array(unique_values)
            if isinstance(parsed_unique_values[0], Real):  # upcast to float for comparison
                parsed_unique_values = parsed_unique_values.astype(float)
            elif str(parsed_unique_values.dtype)[:2] == "<U":  # parse strings as all lower-case
                for j in range(2):
                    parsed_unique_values[j] = parsed_unique_values[j].lower()
            pairs_to_check = [
                [1.0, 0.0],
                ["yes", "no"],
                ["y", "n"],
                ["true", "false"],
                ["t", "f"],
                ["hit", "miss"],
            ]
            if any([set(parsed_unique_values) == set(pair) for pair in pairs_to_check]):  # type: ignore
                saved_bytes = (unique_values.dtype.itemsize - 1) * np.prod(
                    get_data_shape(data=column.data, strict_no_data_load=True)
                )
                if unique_values.dtype == "float":
                    print_dtype = "floats"
                elif unique_values.dtype == "int":
                    print_dtype = "integers"
                elif str(unique_values.dtype)[:2] == "<U":
                    print_dtype = "strings"
                else:
                    print_dtype = f"{unique_values.dtype}"
                yield InspectorMessage(
                    message=(
                        f"Column '{column.name}' uses '{print_dtype}' but has binary values {unique_values}. Consider "
                        "making it boolean instead and renaming the column to start with 'is_'; doing so will "
                        f"save {format_byte_size(byte_size=saved_bytes)}."
                    )
                )
    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_single_row(
    table: DynamicTable,
    exclude_types: Optional[tuple] = None,
    exclude_names: Optional[tuple[str]] = None,
) -> Optional[InspectorMessage]:
    """
    Check if DynamicTable has only a single row; may be better represented by another data type.

    Skips the Units table since it is OK to have only a single spiking unit.
    Skips the Electrode table since it is OK to have only a single electrode.
    """
    exclude_types = exclude_types or (Units,)
    exclude_names = exclude_names or ("electrodes",)

    if any((isinstance(table, exclude_type) for exclude_type in exclude_types)):
        return None
    if any((table.name == exclude_name for exclude_name in exclude_names)):
        return None
    if len(table.id) == 1:
        return InspectorMessage(
            message="This table has only a single row; it may be better represented by another data type."
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_table_values_for_dict(
    table: DynamicTable, nelems: Optional[int] = NELEMS
) -> Optional[Iterable[InspectorMessage]]:
    """Check if any values in a row or column of a table contain a string casting of a Python dictionary."""
    if len(table.id) == 0:
        return None  # an empty table is reported by check_empty_table

    for column in table.columns:
        if not hasattr(column, "data") or isinstance(column, VectorIndex) or not isinstance(column.data[0], str):
            continue
        for string in cache_data_selection(data=column.data, selection=slice(nelems)):
            if is_dict_in_string(string=string):
                message = (
                    f"The column '{column.name}' contains a string value that contains a dictionary! Please "
                    "unpack dictionaries as additional rows or columns of the table."
                )
                if is_string_json_loadable(string=string):
                    message += " This string is also JSON loadable, so call `json.loads(...)` on the string to unpack."
                yield InspectorMessage(message=message)

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_col_not_nan(table: DynamicTable, nelems: Optional[int] = NELEMS) -> Optional[Iterable[InspectorMessage]]:
    """Check if all the values in a single column of a table are NaN."""
    if len(table.id) == 0:
        return None  # an empty table is reported by check_empty_table

    for column in table.columns:
        if (
            not hasattr(column, "data")
            or isinstance(column, VectorIndex)
            or not np.issubdtype(np.array(column[0]).dtype, np.floating)
        ):
            continue
        if nelems is not None and not all(np.isnan(column[:nelems]).flatten()):
            continue

        slice_by = np.ceil(len(column.data) / nelems).astype(int) if nelems else None
        message = f"Column '{column.name}' might have all NaN values. Consider removing it from the table."
        message = message.replace("might have", "has") if nelems is None or slice_by == 1 else message
        if all(np.isnan(column[slice(0, None, slice_by)]).flatten()):
            yield InspectorMessage(message=message)

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=DynamicTable)
def check_ids_unique(table: DynamicTable, nelems: Optional[int] = NELEMS) -> Optional[InspectorMessage]:
    """
    Ensure that the values of the id attribute of a DynamicTable are unique.

    Best Practice: :ref:`best_practice_unique_dynamic_table_ids`

    Parameters
    ----------
    table: DynamicTable
    nelems: int, optional
        Only inspect the first {nelems} elements

    Returns
    -------

    """
    data = table.id[:nelems]
    if len(set(data)) != len(data):
        return InspectorMessage(message="This table has ids that are not unique.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_table_time_columns_are_not_negative(table: DynamicTable) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that time columns are not negative.

    Best Practice: :ref:`best_practice_global_time_reference`

    Parameters
    ----------
    table: DynamicTable
    """
    if len(table.id) == 0:
        return None  # an empty table is reported by check_empty_table

    for column_name in table.colnames:
        if column_name.endswith("_time"):
            first_timestamp = table[column_name][0]
            first_timestamp_array = np.asarray(first_timestamp)  # handle array or scalar data
            if np.any(first_timestamp_array < 0):
                yield InspectorMessage(
                    message=f"Timestamps in column {column_name} should not be negative."
                    " It is recommended to align the `session_start_time` or `timestamps_reference_time` to be the earliest time value that occurs in the data, and shift all other signals accordingly."
                )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=TimeIntervals)
def check_time_intervals_duration(
    time_intervals: TimeIntervals, duration_threshold: float = MAX_DURATION
) -> Optional[InspectorMessage]:
    """
    Check if the duration spanned by time columns in a TimeIntervals table exceeds a threshold.

    This check examines start_time, stop_time, and any other columns ending in _time.

    Best Practice: :ref:`best_practice_time_interval_time_columns`

    Parameters
    ----------
    time_intervals: TimeIntervals
        The table to check
    duration_threshold: float, optional
        Maximum expected duration in seconds. Default is 1 year (365.25 days).
    """
    if len(time_intervals.id) == 0:
        return None

    start_times = []
    stop_times = []

    # Check for start_time and stop_time columns
    start_times.append(float(np.nanmin(time_intervals["start_time"][:NELEMS])))
    stop_times.append(float(np.nanmax(time_intervals["stop_time"][-NELEMS:])))

    # Check for other time columns
    for column_name in time_intervals.colnames:
        if (
            column_name.endswith("_time")
            and column_name not in ["start_time", "stop_time"]
            and len(time_intervals[column_name]) > 0
        ):
            data = time_intervals[column_name]
            head = data[:NELEMS]
            tail = data[-NELEMS:]
            head_all_nan = np.all(np.isnan(head))
            tail_all_nan = np.all(np.isnan(tail))
            if head_all_nan and tail_all_nan:
                continue
            if not head_all_nan:
                start_times.append(float(np.nanmin(head)))
            if not tail_all_nan:
                stop_times.append(float(np.nanmax(tail)))

    if start_times and stop_times:
        duration = np.nanmax(stop_times) - np.nanmin(start_times)

        if duration > duration_threshold:
            duration_years = duration / 31557600.0
            threshold_years = duration_threshold / 31557600.0
            return InspectorMessage(
                message=(
                    f"TimeIntervals table '{time_intervals.name}' has a duration of {duration:.2f} seconds "
                    f"({duration_years:.2f} years), which exceeds the threshold of "
                    f"{duration_threshold:.2f} seconds ({threshold_years:.2f} years). "
                    "Please verify that this is correct."
                )
            )
    return None


def _normalize_categorical_value(value: object) -> object:
    """Normalize a value of a categorical column for comparison against the MeaningsTable entries."""
    if isinstance(value, bytes):
        return value.decode("utf-8")

    return value.item() if isinstance(value, np.generic) else value


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=MeaningsTable)
def check_meanings_table_includes_all_values(
    meanings_table: MeaningsTable, maximum_number_of_listed_values: int = 5
) -> Optional[InspectorMessage]:
    """
    Check that every value of the column annotated by a MeaningsTable has an entry in the table.

    Values are compared by type and value, so the integer 1 does not match an entry for the string "1". The values
    ``None``, NaN, ``""``, and ``"n/a"`` mark missing data and do not need an entry. The reverse is allowed: a
    MeaningsTable may contain entries for values that never occur in the column.

    Best Practice: :ref:`best_practice_meanings_table_includes_all_values`
    """
    known_values = set()
    for value in meanings_table["value"].data[:]:
        normalized_value = _normalize_categorical_value(value=value)
        known_values.add((type(normalized_value), normalized_value))

    # A dict keeps the order of first appearance, so that the message is deterministic
    missing_values: dict[tuple[type, object], None] = dict()
    for value in meanings_table.target.data[:]:
        normalized_value = _normalize_categorical_value(value=value)
        if normalized_value is None or normalized_value in ("", "n/a"):
            continue
        if isinstance(normalized_value, float) and np.isnan(normalized_value):
            continue
        key = (type(normalized_value), normalized_value)
        if key not in known_values:
            missing_values[key] = None

    if not missing_values:
        return None

    listed_values = ", ".join(repr(value) for _, value in list(missing_values)[:maximum_number_of_listed_values])
    number_of_unlisted_values = len(missing_values) - min(len(missing_values), maximum_number_of_listed_values)
    if number_of_unlisted_values > 0:
        listed_values += f" (and {number_of_unlisted_values} more)"

    return InspectorMessage(
        message=(
            f"Column '{meanings_table.target.name}' contains values that have no entry in its MeaningsTable "
            f"'{meanings_table.name}': {listed_values}. Every value of the annotated column should have "
            "an entry in the 'value' column of the MeaningsTable describing its meaning."
        )
    )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=MeaningsTable)
def check_meanings_table_values_unique(
    meanings_table: MeaningsTable, maximum_number_of_listed_values: int = 5
) -> Optional[InspectorMessage]:
    """
    Check that each value has at most one entry in a MeaningsTable.

    Values are compared by type and value, as in check_meanings_table_includes_all_values.

    Best Practice: :ref:`best_practice_meanings_table_values_unique`
    """
    # A Counter keeps the order of first appearance, so that the message is deterministic
    counts: Counter[tuple[type, object]] = Counter()
    for value in meanings_table["value"].data[:]:
        normalized_value = _normalize_categorical_value(value=value)
        counts[(type(normalized_value), normalized_value)] += 1
    repeated_values = [(value, count) for (_, value), count in counts.items() if count > 1]
    if not repeated_values:
        return None

    listed_values = ", ".join(
        f"{value!r} ({count} entries)" for value, count in repeated_values[:maximum_number_of_listed_values]
    )
    number_of_unlisted_values = len(repeated_values) - min(len(repeated_values), maximum_number_of_listed_values)
    if number_of_unlisted_values > 0:
        listed_values += f" (and {number_of_unlisted_values} more)"

    return InspectorMessage(
        message=(
            f"MeaningsTable '{meanings_table.name}' repeats values in its 'value' column: {listed_values}. "
            "Each value should have exactly one entry, so that its meaning is unambiguous."
        )
    )
