"""Check functions that can apply to any descendant of DynamicTable."""
from numbers import Real
from typing import List, Optional

import numpy as np
from hdmf.common import DynamicTable, DynamicTableRegion, VectorIndex
from hdmf.utils import get_data_shape
from pynwb.file import TimeIntervals, Units

from ..register_checks import register_check, InspectorMessage, Importance
from ..utils import (
    _cache_data_selection,
    format_byte_size,
    is_ascending_series,
    is_dict_in_string,
    is_string_json_loadable,
)


@register_check(importance=Importance.CRITICAL, neurodata_type=DynamicTableRegion)
def check_dynamic_table_region_data_validity(dynamic_table_region: DynamicTableRegion, nelems=200):
    """Check if a DynamicTableRegion is valid."""
    if np.any(np.asarray(dynamic_table_region.data[:nelems]) > len(dynamic_table_region.table)):
        return InspectorMessage(
            message=(
                f"Some elements of {dynamic_table_region.name} are out of range because they are greater than the "
                "length of the target table. Note that data should contain indices, not ids."
            )
        )
    if np.any(np.asarray(dynamic_table_region.data[:nelems]) < 0):
        return InspectorMessage(
            message=f"Some elements of {dynamic_table_region.name} are out of range because they are less than 0."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_empty_table(table: DynamicTable):
    """Check if a DynamicTable is empty."""
    if len(table.id) == 0:
        return InspectorMessage(message="This table has no data added to it.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_interval_time_columns(time_intervals: TimeIntervals, nelems: int = 200):
    """
    Check that time columns are in ascending order.

    Parameters
    ----------
    time_intervals: TimeIntervals
    nelems: int
        Only check the first {nelems} elements. This is useful in case there columns are
        very long so you don't need to load the entire array into memory. Use None to
        load the entire arrays.
    """
    unsorted_cols = []
    for column in time_intervals.columns:
        if column.name[-5:] == "_time":
            if not is_ascending_series(column.data, nelems):
                unsorted_cols.append(column.name)
    if unsorted_cols:
        return InspectorMessage(
            message=(
                f"{unsorted_cols} are time columns but the values are not in ascending order."
                "All times should be in seconds with respect to the session start time."
            )
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_intervals_stop_after_start(time_intervals: TimeIntervals, nelems: int = 200):
    """
    Check that all stop times on a TimeInterval object occur after their corresponding start times.

    Best Practice: :ref:`best_practice_time_interval_time_columns`

    Parameters
    ----------
    time_intervals: TimeIntervals
    nelems: int
        Only check the first {nelems} elements. This is useful in case there columns are
        very long so you don't need to load the entire array into memory. Use None to
        load the entire arrays.
    """
    if np.any(
        np.asarray(_cache_data_selection(data=time_intervals["stop_time"].data, selection=slice(nelems)))
        - np.asarray(_cache_data_selection(data=time_intervals["start_time"].data, selection=slice(nelems)))
        < 0
    ):
        return InspectorMessage(
            message=(
                "stop_times should be greater than start_times. Make sure the stop times are with respect to the "
                "session start time."
            )
        )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_column_binary_capability(table: DynamicTable, nelems: int = 200):
    """
    Check each column of a table to see if the data could be set as a boolean dtype.

    Parameters
    ----------
    time_intervals: DynamicTable
    nelems: int
        Only check the first {nelems} elements. This is useful in case there columns are
        very long so you don't need to load the entire array into memory. Use None to
        load the entire arrays.
    """
    for column in table.columns:
        if hasattr(column, "data") and not isinstance(column, VectorIndex):
            if np.asarray(column.data[0]).itemsize == 1:
                continue  # already boolean, int8, or uint8
            try:
                unique_values = np.unique(_cache_data_selection(data=column.data, selection=slice(nelems)))
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
            if any([set(parsed_unique_values) == set(pair) for pair in pairs_to_check]):
                saved_bytes = (unique_values.dtype.itemsize - 1) * np.product(
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


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_single_row(
    table: DynamicTable,
    exclude_types: Optional[list] = (Units,),
    exclude_names: Optional[List[str]] = ("electrodes",),
):
    """
    Check if DynamicTable has only a single row; may be better represented by another data type.

    Skips the Units table since it is OK to have only a single spiking unit.
    Skips the Electrode table since it is OK to have only a single electrode.
    """
    if any((isinstance(table, exclude_type) for exclude_type in exclude_types)):
        return
    if any((table.name == exclude_name for exclude_name in exclude_names)):
        return
    if len(table.id) == 1:
        return InspectorMessage(
            message="This table has only a single row; it may be better represented by another data type."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_table_values_for_dict(table: DynamicTable, nelems: int = 200):
    """Check if any values in a row or column of a table contain a string casting of a Python dictionary."""
    for column in table.columns:
        if not hasattr(column, "data") or isinstance(column, VectorIndex) or not isinstance(column.data[0], str):
            continue
        for string in _cache_data_selection(data=column.data, selection=slice(nelems)):
            if is_dict_in_string(string=string):
                message = (
                    f"The column '{column.name}' contains a string value that contains a dictionary! Please "
                    "unpack dictionaries as additional rows or columns of the table."
                )
                if is_string_json_loadable(string=string):
                    message += " This string is also JSON loadable, so call `json.loads(...)` on the string to unpack."
                yield InspectorMessage(message=message)


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_col_not_nan(table: DynamicTable, nelems: Optional[int] = 200):
    """Check if all of the values in a single column of a table are NaN."""
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
