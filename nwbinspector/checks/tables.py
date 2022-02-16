"""Check functions that can apply to any descendant of DynamicTable."""
from hdmf.common import DynamicTable
import numpy as np
from pynwb.file import TimeIntervals

from ..register_checks import register_check, InspectorMessage, Importance


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_empty_table(table: DynamicTable):
    """Check if a DynamicTable is empty."""
    if len(table.id) == 0:
        return InspectorMessage(message="This table has no data added to it.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_interval_time_columns(time_intervals: TimeIntervals):
    unsorted_cols = []
    for column in time_intervals.columns:
        if column.name[-5:] == "_time":
            if np.any(np.diff(column[:]) < 0):
                unsorted_cols.append(column.name)
    if unsorted_cols:
        return InspectorMessage(
            message=f"{unsorted_cols} are time columns but the values are not in ascending order."
            "All times should be in seconds with respect to the session start time."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=TimeIntervals)
def check_time_intervals_stop_after_start(time_intervals: TimeIntervals):
    if np.any(np.asarray(time_intervals["stop_time"][:]) - np.asarray(time_intervals["start_time"][:]) < 0):
        return InspectorMessage(
            message="stop_times should be greater than start_times. Make sure the stop times are with respect to the "
            "session start time."
        )


# @register_check(importance="Best Practice Violation", neurodata_type=pynwb.core.DynamicTable)
# def check_single_tables(nwbfile):
#     """Check if DynamicTable has only a single row; may be better represented by another data type."""
#     for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
#         if len(tab.id) == 1:
#             print("NOTE: '%s' %s has one row" % (tab.name, type(tab).__name__))
#             continue


# @register_check(importance="Best Practice Violation", neurodata_type=pynwb.core.DynamicTable)
# def check_column_data_is_not_none(nwbfile):
#     """Check column values in DynamicTable to enssure they are not None."""
#     for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
#         for col in tab.columns:
#             if not isinstance(col, hdmf.common.table.DynamicTableRegion) and col.data is None:
#                 return f"'{tab.name}' {type(tab).__name__} column {col.name} data is None"
#                 # continue
#                 # TODO: think about how to handle this continuable logic in new refactor


# # TODO, continue to break this up
# @nwbinspector_check(severity=1, neurodata_type=pynwb.core.DynamicTable)
# def check_column_table(nwbfile):
#     """Check column values in DynamicTable objects"""
#     for tab in all_of_type(nwbfile, pynwb.core.DynamicTable):
#         for col in tab.columns:
#             if isinstance(col, hdmf.common.table.DynamicTableRegion):
#                 continue

#             if col.name.endswith("index"):  # skip index columns
#                 continue

#             if isinstance(col.data, hdmf.backends.hdf5.h5_utils.DatasetOfReferences):  # TODO find a better way?
#                 continue

#             uniq = np.unique(col.data)
#             # TODO only do this for optional columns
#             if len(uniq) == 1:
#                 error_code = "A101"
#                 print(
#                     "- %s: '%s' %s column '%s' data has all values = %s"
#                     % (error_code, tab.name, type(tab).__name__, col.name, uniq[0])
#                 )
#             elif np.array_equal(uniq, [0.0, 1.0]):
#                 if col.data.dtype.type != np.bool_:
#                     error_code = "A101"
#                     print(
#                         "- %s: '%s' %s column '%s' data should be type boolean instead of %s"
#                         % (
#                             error_code,
#                             tab.name,
#                             type(tab).__name__,
#                             col.name,
#                             col.data.dtype,
#                         )
#                     )
#             elif len(uniq) == 2:
#                 error_code = "A101"
#                 print(
#                     (
#                         "- %s: '%s' %s column '%s' data has only unique values %s. Consider storing the data "
#                         "as boolean."
#                     )
#                     % (error_code, tab.name, type(tab).__name__, col.name, uniq)
#                 )
