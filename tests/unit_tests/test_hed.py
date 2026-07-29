"""Tests for the HED checks.

These require the ``ndx-hed`` package, which is an optional dependency of the NWB Inspector
(`pip install nwbinspector[hed]`). The whole module is skipped when it is not installed.
"""

from datetime import datetime, timezone

import pytest
from hdmf.common import DynamicTable, MeaningsTable, VectorData
from pynwb import NWBFile

from nwbinspector import Importance, InspectorMessage, default_check_registry
from nwbinspector.checks import (
    check_hed_annotations_valid,
    check_hed_lab_metadata_exists,
    check_hed_value_vector_not_in_meanings_table,
)

pytest.importorskip("ndx_hed", reason="The 'ndx-hed' package is required for the HED checks.")

from ndx_hed import HedLabMetaData, HedTags, HedValueVector  # noqa: E402

HED_SCHEMA_VERSION = "8.4.0"


def _make_nwbfile(add_hed_lab_meta_data: bool = True) -> NWBFile:
    nwbfile = NWBFile(
        session_description="Testing HED annotations.",
        identifier="hed_test",
        session_start_time=datetime(2020, 1, 1, tzinfo=timezone.utc),
    )
    if add_hed_lab_meta_data:
        nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version=HED_SCHEMA_VERSION))

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


def test_check_hed_lab_metadata_exists_pass():
    nwbfile = _make_nwbfile()
    _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "Agent-action"])

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


def test_check_hed_lab_metadata_exists_lists_only_a_few_columns():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    for table_index in range(5):
        _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event"], name=f"events_{table_index}")

    message = check_hed_lab_metadata_exists(nwbfile=nwbfile).message
    assert "'HED' of table 'events_0'" in message
    assert "'HED' of table 'events_2'" in message
    assert "'HED' of table 'events_3'" not in message
    assert "(and 2 more)" in message


def test_check_hed_lab_metadata_exists_skipped_without_hed_columns():
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    nwbfile.add_acquisition(
        DynamicTable(
            name="events",
            description="Events without HED annotations.",
            columns=[VectorData(name="event_time", description="Event times.", data=[1.0, 2.0])],
        )
    )

    assert check_hed_lab_metadata_exists(nwbfile=nwbfile) is None


def test_check_hed_annotations_valid_pass():
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event, Visual-presentation", "Agent-action"])

    assert check_hed_annotations_valid(table=table) is None


def test_check_hed_annotations_valid_skipped_without_hed_columns():
    nwbfile = _make_nwbfile()
    table = DynamicTable(
        name="events",
        description="Events without HED annotations.",
        columns=[VectorData(name="event_time", description="Event times.", data=[1.0, 2.0])],
    )
    nwbfile.add_acquisition(table)

    assert check_hed_annotations_valid(table=table) is None


def test_check_hed_annotations_valid_skipped_without_lab_metadata():
    """A file without a HedLabMetaData cannot be validated, which check_hed_lab_metadata_exists reports."""
    nwbfile = _make_nwbfile(add_hed_lab_meta_data=False)
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["NonExistentEvent"])

    assert check_hed_annotations_valid(table=table) is None


def test_check_hed_annotations_valid_fail():
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["Sensory-event", "NonExistentEvent", "AnotherBadTag"])

    messages = list(check_hed_annotations_valid(table=table))

    assert len(messages) == 2
    assert messages[0] == InspectorMessage(
        message=(
            "HED validation error in column 'HED', row 1 (TAG_INVALID): "
            "'NonExistentEvent' in NonExistentEvent is not a valid base HED tag."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_hed_annotations_valid",
        object_type="DynamicTable",
        object_name="events",
        location=None,
    )
    assert "'AnotherBadTag'" in messages[1].message
    assert "row 2" in messages[1].message


def test_check_hed_annotations_valid_reports_the_row_of_the_offending_tag():
    nwbfile = _make_nwbfile()
    tags = ["Sensory-event"] * 7 + ["NonExistentEvent"]
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=tags)

    messages = list(check_hed_annotations_valid(table=table))

    assert len(messages) == 1
    assert f"row {tags.index('NonExistentEvent')} " in messages[0].message


def test_check_hed_annotations_valid_collapses_repeats_of_the_same_error():
    """The same mistake repeated down a column is reported by the validator once per row, but once here."""
    nwbfile = _make_nwbfile()
    table = _add_hed_tags_table(nwbfile=nwbfile, tags=["NonExistentEvent"] * 4)

    messages = list(check_hed_annotations_valid(table=table))

    assert len(messages) == 1
    assert "This error occurs on 4 rows; only the first is reported." in messages[0].message


def test_check_hed_annotations_valid_of_a_value_vector():
    nwbfile = _make_nwbfile()
    table = DynamicTable(
        name="trials",
        description="Trials with an invalid HED value template.",
        columns=[
            VectorData(name="trial_id", description="Trial IDs.", data=[1, 2, 3]),
            HedValueVector(
                name="reaction_time",
                description="Response times.",
                data=[500, 700, 300],
                hed="InvalidValueTag/#",
            ),
        ],
    )
    nwbfile.add_acquisition(table)

    messages = list(check_hed_annotations_valid(table=table))

    assert len(messages) == 1
    assert "in column 'reaction_time'" in messages[0].message
    assert "'InvalidValueTag'" in messages[0].message


def _make_meanings_table(annotation_column) -> MeaningsTable:
    target = VectorData(name="response", description="Response codes.", data=["go", "stop"])
    meanings_table = MeaningsTable(target=target, description="Meanings of response codes.")
    meanings_table.add_row(value="go", meaning="A go trial.")
    meanings_table.add_row(value="stop", meaning="A stop trial.")
    meanings_table.add_column(
        name=annotation_column.pop("name"), description="HED annotations of the values.", **annotation_column
    )

    return meanings_table


def test_check_hed_value_vector_not_in_meanings_table_pass():
    meanings_table = _make_meanings_table(
        annotation_column=dict(name="HED", col_cls=HedTags, data=["Sensory-event", "Agent-action"])
    )

    assert check_hed_value_vector_not_in_meanings_table(meanings_table=meanings_table) is None


def test_check_hed_value_vector_not_in_meanings_table_fail():
    meanings_table = _make_meanings_table(
        annotation_column=dict(name="template", col_cls=HedValueVector, data=[1, 2], hed="Duration/# s")
    )

    messages = list(check_hed_value_vector_not_in_meanings_table(meanings_table=meanings_table))

    assert messages == [
        InspectorMessage(
            message=(
                "Column 'template' of MeaningsTable 'response_meanings' is a HedValueVector, "
                "which is not allowed in a MeaningsTable. A MeaningsTable assigns a HED annotation to "
                "each individual value of a categorical column, so its annotations must be complete "
                "HED strings stored in a HedTags column."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_hed_value_vector_not_in_meanings_table",
            object_type="MeaningsTable",
            object_name="response_meanings",
            location="/",
        )
    ]


def test_hed_checks_are_registered():
    assert "check_hed_lab_metadata_exists" in default_check_registry
    assert "check_hed_annotations_valid" in default_check_registry
    assert "check_hed_value_vector_not_in_meanings_table" in default_check_registry
