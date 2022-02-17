from unittest import TestCase

import pytest
from hdmf.common import DynamicTable, DynamicTableRegion
from pynwb.file import TimeIntervals

from nwbinspector import (
    check_empty_table,
    check_time_interval_time_columns,
    check_time_intervals_stop_after_start,
    check_dynamic_table_region_data_validity,
)
from nwbinspector.register_checks import InspectorMessage, Importance, Severity


class TestCheckDynamicTableRegion(TestCase):

    def setUp(self):
        self.table = DynamicTable(name="test_table", description="")
        self.table.add_column(name="test_column", description="")
        for _ in range(10):
            self.table.add_row(test_column=1)

    def test_check_dynamic_table_region_data_validity_lt_zero(self):
        dynamic_table_region = DynamicTableRegion(name="dyn_tab", description="desc", data=[-1, 0], table=self.table)
        assert check_dynamic_table_region_data_validity(dynamic_table_region) == InspectorMessage(
            severity=Severity.NO_SEVERITY,
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
            severity=Severity.NO_SEVERITY,
            message="Some elements of dyn_tab are out of range because they are greater than the length of the target table. Note that data should contain indices, not ids.",
            importance=Importance.CRITICAL,
            check_function_name="check_dynamic_table_region_data_validity",
            object_type="DynamicTableRegion",
            object_name="dyn_tab",
            location="/",
        )

    def test_pass_check_dynamic_table_region_data(self):
        dynamic_table_region = DynamicTableRegion(name="dyn_tab", description="desc", data=[0, 0, 2], table=self.table)
        assert check_dynamic_table_region_data_validity(dynamic_table_region) is None


def test_check_empty_table_with_data():
    table = DynamicTable(name="test_table", description="")
    table.add_column(name="test_column", description="")
    table.add_row(test_column=1)
    assert check_empty_table(table=table) is None


def test_check_empty_table_without_data():
    assert check_empty_table(table=DynamicTable(name="test_table", description="")) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
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
        severity=Severity.NO_SEVERITY,
        message="['start_time', 'stop_time'] are time columns but the values are not in ascending order."
        "All times should be in seconds with respect to the session start time.",
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
        severity=Severity.NO_SEVERITY,
        message="stop_times should be greater than start_times. Make sure the stop times are with respect to the "
        "session start time.",
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


@pytest.mark.skip(reason="TODO")
def test_check_single_tables():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_column_data_is_not_none():
    pass
