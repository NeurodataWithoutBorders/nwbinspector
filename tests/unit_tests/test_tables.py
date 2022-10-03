import platform
import json
from unittest import TestCase
from packaging import version

import numpy as np
from hdmf.common import DynamicTable, DynamicTableRegion
from pynwb.file import TimeIntervals, Units, ElectrodeTable, ElectrodeGroup, Device

from nwbinspector import (
    InspectorMessage,
    Importance,
    check_empty_table,
    check_time_interval_time_columns,
    check_time_intervals_stop_after_start,
    check_dynamic_table_region_data_validity,
    check_column_binary_capability,
    check_single_row,
    check_table_values_for_dict,
    check_col_not_nan,
)
from nwbinspector.utils import get_package_version


class TestCheckDynamicTableRegion(TestCase):
    def setUp(self):
        self.table = DynamicTable(name="test_table", description="")
        self.table.add_column(name="test_column", description="")
        for _ in range(10):
            self.table.add_row(test_column=1)

    def test_check_dynamic_table_region_data_validity_lt_zero(self):
        dynamic_table_region = DynamicTableRegion(name="dyn_tab", description="desc", data=[-1, 0], table=self.table)
        assert check_dynamic_table_region_data_validity(dynamic_table_region) == InspectorMessage(
            message="Some elements of dyn_tab are out of range because they are less than 0.",
            importance=Importance.CRITICAL,
            check_function_name="check_dynamic_table_region_data_validity",
            object_type="DynamicTableRegion",
            object_name="dyn_tab",
            location="/",
        )

    def test_check_dynamic_table_region_data_validity_gt_len(self):
        dynamic_table_region = DynamicTableRegion(name="dyn_tab", description="desc", data=[0, 20], table=self.table)
        assert check_dynamic_table_region_data_validity(dynamic_table_region) == InspectorMessage(
            message=(
                "Some elements of dyn_tab are out of range because they are greater than the length of the target "
                "table. Note that data should contain indices, not ids."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_dynamic_table_region_data_validity",
            object_type="DynamicTableRegion",
            object_name="dyn_tab",
            location="/",
        )

    def test_pass_check_dynamic_table_region_data(self):
        dynamic_table_region = DynamicTableRegion(name="dyn_tab", description="desc", data=[0, 1, 2], table=self.table)
        assert check_dynamic_table_region_data_validity(dynamic_table_region) is None


def test_check_empty_table_with_data():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=1)
    assert check_empty_table(table=table) is None


def test_check_empty_table_without_data():
    assert check_empty_table(table=DynamicTable(name="test_table", description="")) == InspectorMessage(
        message="This table has no data added to it.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_empty_table",
        object_type="DynamicTable",
        object_name="test_table",
        location="/",
    )


def test_check_time_interval_time_columns():
    time_intervals = TimeIntervals(name="test_table", description="desc")
    time_intervals.add_row(start_time=2.0, stop_time=3.0)
    time_intervals.add_row(start_time=1.0, stop_time=2.0)

    assert check_time_interval_time_columns(time_intervals) == InspectorMessage(
        message=(
            "['start_time', 'stop_time'] are time columns but the values are not in ascending order."
            "All times should be in seconds with respect to the session start time."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_time_interval_time_columns",
        object_type="TimeIntervals",
        object_name="test_table",
        location="/",
    )


def test_pass_check_time_interval_time_columns():
    time_intervals = TimeIntervals(name="test_table", description="desc")
    time_intervals.add_row(start_time=1.0, stop_time=2.0)
    time_intervals.add_row(start_time=2.0, stop_time=3.0)

    assert check_time_interval_time_columns(time_intervals) is None


def test_check_time_intervals_stop_after_start():
    time_intervals = TimeIntervals(name="test_table", description="desc")
    time_intervals.add_row(start_time=2.0, stop_time=1.5)
    time_intervals.add_row(start_time=3.0, stop_time=1.5)
    assert check_time_intervals_stop_after_start(time_intervals) == InspectorMessage(
        message=(
            "stop_times should be greater than start_times. Make sure the stop times are with respect to the "
            "session start time."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_time_intervals_stop_after_start",
        object_type="TimeIntervals",
        object_name="test_table",
        location="/",
    )


def test_pass_check_time_intervals_stop_after_start():
    time_intervals = TimeIntervals(name="test_table", description="desc")
    time_intervals.add_row(start_time=2.0, stop_time=2.5)
    time_intervals.add_row(start_time=3.0, stop_time=3.5)
    assert check_time_intervals_stop_after_start(time_intervals) is None


class TestCheckBinaryColumns(TestCase):
    def setUp(self):
        self.table = DynamicTable(name="test_table", description="")

    def test_non_binary_pass(self):
        self.table.add_column(name="test_col", description="")
        for x in [1.0, 2.0, 3.0]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) is None

    def test_array_of_non_binary_pass(self):
        self.table.add_column(name="test_col", description="")
        for x in [[1.0, 2.0], [2.0, 3.0], [1.0, 2.0]]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) is None

    def test_jagged_array_of_non_binary_pass(self):
        self.table.add_column(name="test_col", description="", index=True)
        for x in [[1.0, 2.0], [1.0, 2.0, 3.0], [1.0, 2.0]]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) is None

    def test_no_saved_bytes_pass(self):
        self.table.add_column(name="test_col", description="")
        for x in np.array([1, 0, 1, 0], dtype="uint8"):
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) is None

    def test_binary_floats_fail(self):
        self.table.add_column(name="test_col", description="")
        for x in [1.0, 0.0, 1.0, 0.0, 1.0]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) == [
            InspectorMessage(
                message=(
                    "Column 'test_col' uses 'floats' but has binary values [0. 1.]. Consider making it boolean instead "
                    "and renaming the column to start with 'is_'; doing so will save 35.00B."
                ),
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_column_binary_capability",
                object_type="DynamicTable",
                object_name="test_table",
                location="/",
            )
        ]

    def test_binary_int_fail(self):
        self.table.add_column(name="test_col", description="")
        for x in [1, 0, 1, 0, 1]:
            self.table.add_row(test_col=x)
        if platform.system() == "Windows":
            platform_saved_bytes = "15.00B"
        else:
            platform_saved_bytes = "35.00B"
        assert check_column_binary_capability(table=self.table) == [
            InspectorMessage(
                message=(
                    "Column 'test_col' uses 'integers' but has binary values [0 1]. Consider making it boolean "
                    f"instead and renaming the column to start with 'is_'; doing so will save {platform_saved_bytes}."
                ),
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_column_binary_capability",
                object_type="DynamicTable",
                object_name="test_table",
                location="/",
            )
        ]

    def test_binary_string_fail(self):
        self.table.add_column(name="test_col", description="")
        for x in ["YES", "NO", "NO", "YES"]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) == [
            InspectorMessage(
                message=(
                    "Column 'test_col' uses 'strings' but has binary values ['NO' 'YES']. Consider making it boolean "
                    "instead and renaming the column to start with 'is_'; doing so will save 44.00B."
                ),
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_column_binary_capability",
                object_type="DynamicTable",
                object_name="test_table",
                location="/",
            )
        ]

    def test_binary_string_pass(self):
        self.table.add_column(name="test_col", description="")
        for x in ["testing", "testingAgain", "MoreTesting", "testing"]:
            self.table.add_row(test_col=x)
        assert check_column_binary_capability(table=self.table) is None


def test_check_single_row_pass():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=1)
    table.add_row(test_column=2)
    assert check_single_row(table=table) is None


def test_check_single_row_ignore_units():
    table = Units(
        name="Units",
    )  # default name when building through nwbfile
    table.add_unit(spike_times=[1, 2, 3])
    assert check_single_row(table=table) is None


def test_check_single_row_ignore_electrodes():
    table = ElectrodeTable(
        name="electrodes",
    )  # default name when building through nwbfile
    if get_package_version(name="pynwb") >= version.Version("2.1.0"):
        table.add_row(
            location="unknown",
            group=ElectrodeGroup(
                name="test_group", description="", device=Device(name="test_device"), location="unknown"
            ),
            group_name="test_group",
        )
    else:
        table.add_row(
            x=np.nan,
            y=np.nan,
            z=np.nan,
            imp=np.nan,
            location="unknown",
            filtering="unknown",
            group=ElectrodeGroup(
                name="test_group", description="", device=Device(name="test_device"), location="unknown"
            ),
            group_name="test_group",
        )
    assert check_single_row(table=table) is None


def test_check_single_row_fail():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=1)
    assert check_single_row(table=table) == InspectorMessage(
        message="This table has only a single row; it may be better represented by another data type.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_single_row",
        object_type="DynamicTable",
        object_name="test_table",
        location="/",
    )


def test_check_table_values_for_dict_non_str():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=123)
    assert check_table_values_for_dict(table=table) is None


def test_check_table_values_for_dict_pass():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column="123")
    assert check_table_values_for_dict(table=table) is None


def test_check_table_values_for_dict_fail():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=str(dict(a=1)))
    assert check_table_values_for_dict(table=table)[0] == InspectorMessage(
        message=(
            "The column 'test_column' contains a string value that contains a dictionary! Please unpack "
            "dictionaries as additional rows or columns of the table."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_table_values_for_dict",
        object_type="DynamicTable",
        object_name="test_table",
        location="/",
    )


def test_check_table_values_for_dict_json_case_fail():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=json.dumps(dict(a=1)))
    assert check_table_values_for_dict(table=table) == [
        InspectorMessage(
            message=(
                "The column 'test_column' contains a string value that contains a dictionary! Please unpack "
                "dictionaries as additional rows or columns of the table. This string is also JSON loadable, so call "
                "`json.loads(...)` on the string to unpack."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_table_values_for_dict",
            object_type="DynamicTable",
            object_name="test_table",
            location="/",
        )
    ]


def test_check_col_not_nan_pass():
    table = DynamicTable(name="test_table", description="")
    for name in ["test_column_not_nan", "test_column_string"]:
        table.add_column(name=name, description="")
    table.add_row(test_column_not_nan=1.0, test_column_string="abc")
    assert check_col_not_nan(table=table) is None


def test_check_col_not_nan_fail():
    """Addition of test_integer_type included from issue 241."""
    table = DynamicTable(name="test_table", description="")
    for name in ["test_column_not_nan_1", "test_column_nan_1", "test_integer_type", "test_column_nan_2"]:
        table.add_column(name=name, description="")
    for _ in range(400):
        table.add_row(
            test_column_not_nan_1=1.0, test_column_nan_1=np.nan, test_integer_type=1, test_column_nan_2=np.nan
        )
    assert check_col_not_nan(table=table) == [
        InspectorMessage(
            message="Column 'test_column_nan_1' might have all NaN values. Consider removing it from the table.",
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_col_not_nan",
            object_type="DynamicTable",
            object_name="test_table",
            location="/",
            file_path=None,
        ),
        InspectorMessage(
            message="Column 'test_column_nan_2' might have all NaN values. Consider removing it from the table.",
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_col_not_nan",
            object_type="DynamicTable",
            object_name="test_table",
            location="/",
            file_path=None,
        ),
    ]


def test_check_col_not_nan_fail_span_all_data():
    """Addition of test_integer_type included from issue 241."""
    table = DynamicTable(name="test_table", description="")
    for name in ["test_column_not_nan_1", "test_column_nan_1", "test_integer_type", "test_column_nan_2"]:
        table.add_column(name=name, description="")
    for _ in range(180):
        table.add_row(
            test_column_not_nan_1=1.0, test_column_nan_1=np.nan, test_integer_type=1, test_column_nan_2=np.nan
        )
    assert check_col_not_nan(table=table) == [
        InspectorMessage(
            message="Column 'test_column_nan_1' has all NaN values. Consider removing it from the table.",
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_col_not_nan",
            object_type="DynamicTable",
            object_name="test_table",
            location="/",
            file_path=None,
        ),
        InspectorMessage(
            message="Column 'test_column_nan_2' has all NaN values. Consider removing it from the table.",
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_col_not_nan",
            object_type="DynamicTable",
            object_name="test_table",
            location="/",
            file_path=None,
        ),
    ]
