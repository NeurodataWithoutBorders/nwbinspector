import pytest
from hdmf.common import DynamicTable
from pynwb.file import TimeIntervals

from nwbinspector import check_empty_table, check_time_interval_time_columns, check_time_intervals_stop_after_start
from nwbinspector.register_checks import InspectorMessage, Importance, Severity


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
