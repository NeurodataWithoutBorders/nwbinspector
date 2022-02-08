import pytest
from hdmf.common import DynamicTable

from nwbinspector import check_empty_table
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


@pytest.mark.skip(reason="TODO")
def test_check_single_tables():
    pass


@pytest.mark.skip(reason="TODO")
def test_check_column_data_is_not_none():
    pass
