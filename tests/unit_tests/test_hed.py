"""Tests for the HED checks.

These require the ``ndx-hed`` package, which is an optional dependency of the NWB Inspector
(`pip install nwbinspector[hed]`). The whole module is skipped when it is not installed.
"""

from datetime import datetime, timezone

import numpy as np
import pytest
from hdmf.common import DynamicTable, MeaningsTable, VectorData
from pynwb import NWBHDF5IO, NWBFile
from pynwb.event import EventsTable, TimestampVectorData

from nwbinspector import Importance, InspectorMessage, default_check_registry
from nwbinspector.checks import (
    _hed,
    check_hed_annotations_valid,
    check_hed_annotations_warnings,
    check_hed_lab_metadata_exists,
)

pytest.importorskip("ndx_hed", reason="The 'ndx-hed' package is required for the HED checks.")

from ndx_hed import (  # noqa: E402
    HedDurationVector,
    HedLabMetaData,
    HedTags,
    HedValueVector,
)
from ndx_hed.utils import bids2nwb  # noqa: E402

HED_SCHEMA_VERSION = "8.4.0"
DEFINITIONS = "(Definition/Go-cue, (Sensory-event, Visual-presentation))"


def _make_nwbfile(add_hed_lab_meta_data: bool = True) -> NWBFile:
    nwbfile = NWBFile(
        session_description="Testing HED annotations.",
        identifier="hed_test",
        session_start_time=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    if add_hed_lab_meta_data:
        nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version=HED_SCHEMA_VERSION, definitions=DEFINITIONS))

    return nwbfile


def _add_hed_tags_table(nwbfile: NWBFile, tags: list, name: str = "events") -> DynamicTable:
    table = DynamicTable(
        name=name,
        description="Events annotated with HED.",
        columns=[
            VectorData(name="event_time", description="Event times.", data=list(range(len(tags)))),
            HedTags(data=tags),
        ],
    )
    nwbfile.add_acquisition(table)

    return table


def _add_categorical_table(
    nwbfile: NWBFile, values: list, hed_by_value: dict, name: str = "trials_hed"
) -> DynamicTable:
    table = DynamicTable(
        name=name,
        description="Trials with a categorical condition annotated with HED.",
        columns=[VectorData(name="condition", description="The condition of the trial.", data=values)],
    )
    meanings_table = MeaningsTable(target=table["condition"], description="The meanings of the conditions.")
    meanings_table.add_column(name="HED", description="The HED of each condition.", col_cls=HedTags)
    for value, hed in hed_by_value.items():
        meanings_table.add_row(value=value, meaning=f"The {value} condition.", HED=hed)
    table.add_meanings_table(meanings_table)
    nwbfile.add_acquisition(table)

    return table


def _messages(check_function, table) -> list[str]:
    return [message.message for message in check_function(table=table) or []]


def _expected_message(
    message: str, table: DynamicTable, check_function=check_hed_annotations_valid
) -> InspectorMessage:
    return InspectorMessage(
        message=message,
        importance=check_function.importance,
        check_function_name=check_function.__name__,
        object_type=type(table).__name__,
        object_name=table.name,
        location=None,  # Filled in when the check is run by the inspector
    )


def test_hed_checks_are_registered():
    assert default_check_registry["check_hed_lab_metadata_exists"].importance == Importance.BEST_PRACTICE_VIOLATION
    assert default_check_registry["check_hed_annotations_valid"].importance == Importance.BEST_PRACTICE_VIOLATION
    assert default_check_registry["check_hed_annotations_warnings"].importance == Importance.BEST_PRACTICE_SUGGESTION


# check_hed_lab_metadata_exists


def test_check_hed_lab_metadata_exists_pass():
    nwbfile = _make_nwbfile()
    _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "Agent-action"])

    assert check_hed_lab_metadata_exists(nwbfile=nwbfile) is None


def test_check_hed_lab_metadata_exists_skipped_without_hed_columns():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    nwbfile.add_acquisition(
        DynamicTable(name="plain", description="", columns=[VectorData(name="value", description="", data=[1, 2])])
    )

    assert check_hed_lab_metadata_exists(nwbfile=nwbfile) is None


def test_check_hed_lab_metadata_exists_fail():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "Agent-action"])

    assert check_hed_lab_metadata_exists(nwbfile=nwbfile) == InspectorMessage(
        message=(
            "This file contains HED annotations in column 'HED' of table 'events', but it does not contain a "
            "HedLabMetaData object declaring the version of the HED schema that those annotations use. "
            "Without it the annotations cannot be interpreted or validated. Add one with, for example, "
            "`nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version='8.4.0'))`."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_hed_lab_metadata_exists",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )


def test_check_hed_lab_metadata_exists_finds_hed_in_a_meanings_table():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    _add_categorical_table(nwbfile=nwbfile, values=["go"], hed_by_value={"go": "Sensory-event"})

    message = check_hed_lab_metadata_exists(nwbfile=nwbfile).message
    assert "column 'HED' of table 'condition_meanings'" in message


def test_check_hed_lab_metadata_exists_lists_only_a_few_columns():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    for index in range(5):
        _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event"], name=f"events_{index}")

    message = check_hed_lab_metadata_exists(nwbfile=nwbfile).message
    assert "'HED' of table 'events_0', 'HED' of table 'events_1', 'HED' of table 'events_2' (and 2 more)" in message


# check_hed_annotations_valid


def test_check_hed_annotations_valid_pass():
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(
        nwbfile=nwbfile,
        values=["go", "stop", "go"],
        hed_by_value={"go": "Def/Go-cue", "stop": "Agent-action"},
    )
    table.add_column(name="HED", description="", col_cls=HedTags, data=["Red", "Blue", "Green"])
    table.add_column(name="age", description="", col_cls=HedValueVector, hed="Age/# s", data=[0.1, 0.2, 0.3])

    assert _messages(check_hed_annotations_valid, table) == []
    assert _messages(check_hed_annotations_warnings, table) == []


def test_check_hed_annotations_valid_skipped_without_hed_columns():
    nwbfile = _make_nwbfile()
    table = DynamicTable(name="plain", description="", columns=[VectorData(name="value", description="", data=[1])])
    nwbfile.add_acquisition(table)

    assert _messages(check_hed_annotations_valid, table) == []


def test_check_hed_annotations_valid_skipped_without_lab_metadata():
    """A file without the HED schema version is reported by check_hed_lab_metadata_exists instead."""
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["NotATag"])

    assert _messages(check_hed_annotations_valid, table) == []


def test_check_hed_annotations_valid_skips_the_meanings_table_itself():
    """The HED of a MeaningsTable is validated, and reported, as part of the table whose column it annotates."""
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(nwbfile=nwbfile, values=["go"], hed_by_value={"go": "NotATag"})

    assert _messages(check_hed_annotations_valid, table.meanings_tables["condition_meanings"]) == []
    assert len(_messages(check_hed_annotations_valid, table)) == 1


def test_check_hed_annotations_valid_hed_column():
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "InvalidEventTag"])

    assert list(check_hed_annotations_valid(table=table)) == [
        _expected_message(
            message=(
                "HED error TAG_INVALID in column 'HED' at row index 1: 'InvalidEventTag' in InvalidEventTag is "
                "not a valid base HED tag."
            ),
            table=table,
        )
    ]


def test_check_hed_annotations_valid_collapses_rows_with_the_same_value():
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "Badtag"] * 500)

    assert _messages(check_hed_annotations_valid, table) == [
        "HED error TAG_INVALID in column 'HED' at row index 1: 'Badtag' in Badtag is not a valid base HED tag. "
        "The same HED string occurs on 500 rows."
    ]


def test_check_hed_annotations_valid_lists_the_values_of_a_value_vector():
    """Each value is a different invalid tag once substituted; they share a cause and are listed in one message."""
    nwbfile = _make_nwbfile()
    table = DynamicTable(name="responses", description="")
    table.add_column(name="age", description="", col_cls=HedValueVector, hed="Age/# s")
    for value in ["old", "young", "old", "adult", "old", "young"]:
        table.add_row(age=value)
    nwbfile.add_acquisition(table)

    messages = _messages(check_hed_annotations_valid, table)
    assert len(messages) == 1
    assert messages[0].startswith("HED error VALUE_INVALID in column 'age': 'Age/old s' has an invalid value portion")
    assert messages[0].endswith(
        "3 different HED strings on 6 rows have this error: 'Age/old s' (row index 0, 3 rows), "
        "'Age/young s' (row index 1, 2 rows), 'Age/adult s' (row index 3)."
    )


def test_check_hed_annotations_valid_lists_different_mistakes_in_the_hed_column():
    nwbfile = _make_nwbfile()
    tags = ["Sensory-event", "Badtag", "Sensory-eventzz", "Badtag"] + [f"Typo-{index}" for index in range(5)]
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=tags)

    assert _messages(check_hed_annotations_valid, table) == [
        "HED error TAG_INVALID in column 'HED': 'Badtag' in Badtag is not a valid base HED tag. 7 different HED "
        "strings on 8 rows have this error: 'Badtag' (row index 1, 2 rows), 'Sensory-eventzz' (row index 2), "
        "'Typo-0' (row index 4), 'Typo-1' (row index 5), 'Typo-2' (row index 6) (and 2 more)."
    ]


def test_check_hed_annotations_valid_value_vector_template():
    nwbfile = _make_nwbfile()
    table = DynamicTable(name="responses", description="")
    table.add_column(name="response_time", description="", col_cls=HedValueVector, hed="InvalidValueTag/#")
    table.add_row(response_time=0.5)
    nwbfile.add_acquisition(table)

    assert _messages(check_hed_annotations_valid, table) == [
        "HED error TAG_INVALID in the HED of column 'response_time': 'InvalidValueTag' in InvalidValueTag/# is "
        "not a valid base HED tag."
    ]


def test_check_hed_annotations_valid_duration_vector_template():
    nwbfile = _make_nwbfile()
    events = EventsTable(
        name="stimuli",
        description="",
        columns=[
            TimestampVectorData(name="timestamp", description="", data=[1.0, 2.0]),
            HedDurationVector(name="duration", description="", hed="(Duration/# s, (Not-a-tag))", data=[0.5, 0.5]),
        ],
    )
    nwbfile.add_events_table(events)

    messages = _messages(check_hed_annotations_valid, events)
    assert len(messages) == 1
    assert messages[0].startswith("HED error TAG_INVALID in the HED of column 'duration': 'Not-a-tag'")


def test_check_hed_annotations_valid_meanings_table():
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(
        nwbfile=nwbfile,
        values=["go", "stop"],
        hed_by_value={"go": "Sensory-eventzz", "stop": "Def/Undefined-cue"},
    )

    assert _messages(check_hed_annotations_valid, table) == [
        "HED error TAG_INVALID in the HED of value 'go' in the MeaningsTable of column 'condition': "
        "'Sensory-eventzz' in Sensory-eventzz is not a valid base HED tag.",
        "HED error DEF_INVALID in the HED of value 'stop' in the MeaningsTable of column 'condition': "
        "A data-recording's Def tag cannot be matched to definition. Tag: 'Def/Undefined-cue'.",
    ]


def test_check_hed_annotations_valid_combined_row():
    """A tag that is valid in each column but repeated once the columns of a row are combined."""
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(
        nwbfile=nwbfile,
        values=["go", "stop", "go"],
        hed_by_value={"go": "Sensory-event", "stop": "Agent-action"},
    )
    table.add_column(name="HED", description="", col_cls=HedTags, data=["Sensory-event"] * 3)

    assert _messages(check_hed_annotations_valid, table) == [
        'HED error TAG_EXPRESSION_REPEATED in the combined HED of rows: Repeated tag - "Sensory-event". 2 rows '
        "have this error: 'Sensory-event,Sensory-event' (row index 0), 'Sensory-event,Sensory-event' (row index 2)."
    ]


def test_check_hed_annotations_valid_value_vector_in_meanings_table():
    nwbfile = _make_nwbfile()
    table = DynamicTable(name="trials_hed", description="")
    table.add_column(name="condition", description="")
    table.add_row(condition="go")
    meanings_table = MeaningsTable(target=table["condition"])
    meanings_table.add_column(name="intensity", description="", col_cls=HedValueVector, hed="Luminance/#")
    meanings_table.add_row(value="go", meaning="Go.", intensity=1.0)
    table.add_meanings_table(meanings_table)
    nwbfile.add_acquisition(table)

    assert _messages(check_hed_annotations_valid, table) == [
        "HED error MEANINGS_VALUE_VECTOR_INVALID: Column 'intensity' of MeaningsTable 'condition_meanings' is a "
        "HedValueVector, which is not allowed in a MeaningsTable. Categorical HED must be complete HED strings "
        "in a HedTags column named 'HED'."
    ]


def test_check_hed_annotations_valid_without_ndx_hed(monkeypatch):
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["NotATag"])
    plain_table = DynamicTable(name="plain", description="", columns=[VectorData(name="v", description="", data=[1])])
    nwbfile.add_acquisition(plain_table)
    monkeypatch.setattr(_hed, "_HAS_NDX_HED", False)

    assert _messages(check_hed_annotations_valid, table) == [
        "This table contains HED annotations, but they were not validated because the 'ndx-hed' package is not "
        "installed. Install it with `pip install nwbinspector[hed]`."
    ]
    assert _messages(check_hed_annotations_valid, plain_table) == []
    assert _messages(check_hed_annotations_warnings, table) == []


# check_hed_annotations_warnings


def test_check_hed_annotations_warnings_extended_tag():
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["Item/My-extension"] * 3)

    assert list(check_hed_annotations_warnings(table=table)) == [
        _expected_message(
            message=(
                "HED warning TAG_EXTENDED in column 'HED' at row index 0: Hed tag is extended. '/My-extension' in "
                "Item/My-extension. The same HED string occurs on 3 rows."
            ),
            table=table,
            check_function=check_hed_annotations_warnings,
        )
    ]
    assert _messages(check_hed_annotations_valid, table) == []


def test_check_hed_annotations_warnings_leaves_missing_values_to_the_meanings_check():
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(nwbfile=nwbfile, values=["go", "pause"], hed_by_value={"go": "Sensory-event"})

    assert _messages(check_hed_annotations_warnings, table) == []


# Files read from disk


def test_hed_checks_on_a_file_read_from_disk(tmp_path):
    nwbfile = _make_nwbfile()
    events = EventsTable(
        name="stimuli",
        description="",
        columns=[
            TimestampVectorData(name="timestamp", description="", data=np.arange(4, dtype=float)),
            VectorData(name="condition", description="", data=["go", "stop", "go", "stop"]),
            HedTags(data=["Red", "Blue", "NotATag", "Green"]),
            HedValueVector(name="contrast", description="", hed="Luminance-contrast/#", data=[0.1, 0.2, 0.3, 0.4]),
        ],
    )
    meanings_table = MeaningsTable(target=events["condition"])
    meanings_table.add_column(name="HED", description="", col_cls=HedTags)
    meanings_table.add_row(value="go", meaning="Go.", HED="Def/Go-cue")
    meanings_table.add_row(value="stop", meaning="Stop.", HED="Agent-action")
    events.add_meanings_table(meanings_table)
    nwbfile.add_events_table(events)
    path = tmp_path / "hed.nwb"
    with NWBHDF5IO(path, "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO(path, "r") as io:
        read_nwbfile = io.read()
        read_events = read_nwbfile.events["stimuli"]

        assert check_hed_lab_metadata_exists(nwbfile=read_nwbfile) is None
        assert _messages(check_hed_annotations_valid, read_events) == [
            "HED error TAG_INVALID in column 'HED' at row index 2: 'NotATag' in NotATag is not a valid base HED tag."
        ]


@pytest.mark.xfail(
    not hasattr(bids2nwb, "_value_text"),  # added by the fix, https://github.com/hed-standard/ndx-hed/pull/206
    strict=True,
    raises=TypeError,
    reason="ndx-hed 0.3.0rc1 builds the sidecar of a boolean categorical column read from a file with numpy keys",
)
def test_hed_checks_on_a_boolean_categorical_column_read_from_disk(tmp_path):
    nwbfile = _make_nwbfile()
    table = _add_categorical_table(
        nwbfile=nwbfile, values=[True, False], hed_by_value={True: "Reward", False: "Agent-action"}
    )
    path = tmp_path / "hed_bool.nwb"
    with NWBHDF5IO(path, "w") as io:
        io.write(nwbfile)

    with NWBHDF5IO(path, "r") as io:
        assert _messages(check_hed_annotations_valid, io.read().acquisition[table.name]) == []
