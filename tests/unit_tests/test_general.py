from hdmf.common import DynamicTable

from nwbinspector import InspectorMessage, Importance, check_name_slashes, check_description


def test_check_name_slashes_pass():
    table = DynamicTable(name="test_name", description="")
    assert check_name_slashes(obj=table) is None


def test_check_name_slashes_fail():
    """HDMF/PyNWB forbid "/" in the object names. Might need an external file written in MATLAB to test that?"""
    for x in ["\\"]:
        table = DynamicTable(name=f"test{x}ing", description="")
        assert check_name_slashes(obj=table) == InspectorMessage(
            message="Object name contains slashes.",
            importance=Importance.CRITICAL,
            check_function_name="check_name_slashes",
            object_type="DynamicTable",
            object_name=f"test{x}ing",
            location="/",
        )


def test_check_description_pass():
    table = DynamicTable(name="test", description="testing")
    assert check_description(obj=table) is None


def test_check_description_fail():
    table = DynamicTable(name="test", description="No Description.")
    assert check_description(obj=table) == InspectorMessage(
        message="Description ('No Description.') is a placeholder.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_description",
        object_type="DynamicTable",
        object_name="test",
        location="/",
    )


def test_check_description_missing():
    table = DynamicTable(name="test", description=" ")
    assert check_description(obj=table) == InspectorMessage(
        message="Description is missing.",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_description",
        object_type="DynamicTable",
        object_name="test",
        location="/",
    )
