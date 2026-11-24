from datetime import datetime, timezone
from pathlib import Path

import pytest
from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject

from nwbinspector import Importance, inspect_all
from nwbinspector.checks._subject_consistency import (
    SubjectRecord,
    check_subject_consistency_across_files,
)


def _record(path, subject_id="mouse1", **kwargs):
    return SubjectRecord(file_path=path, subject_id=subject_id, **kwargs)


def _messages(records):
    return list(check_subject_consistency_across_files(records))


def test_genotype_conflict():
    messages = _messages([_record("a.nwb", genotype="WT"), _record("b.nwb", genotype="Anxa1-flp")])
    assert len(messages) == 1
    assert "genotype: 'WT' in 1 file (a.nwb); 'Anxa1-flp' in 1 file (b.nwb)" in messages[0].message
    assert messages[0].importance == Importance.CRITICAL
    assert messages[0].file_path == "a.nwb"


def test_species_conflict_from_reused_subject_id():
    records = [
        _record("a.nwb", subject_id="3", species="Danio rerio"),
        _record("b.nwb", subject_id="3", species="Danionella cerebrum"),
    ]
    assert len(_messages(records)) == 1


def test_several_fields_give_one_message():
    messages = _messages([_record("a.nwb", sex="F", genotype="WT"), _record("b.nwb", sex="M", genotype="Dat-Cre")])
    assert len(messages) == 1
    assert "sex:" in messages[0].message and "genotype:" in messages[0].message


def test_values_are_compared_as_stored():
    records = [_record("a.nwb", sex="M", species="Mus musculus"), _record("b.nwb", sex="M", species="mouse")]
    messages = _messages(records)
    assert len(messages) == 1
    assert "species:" in messages[0].message and "sex:" not in messages[0].message


def test_same_values_are_not_reported():
    records = [_record(f"{i}.nwb", sex="M", species="Mus musculus", genotype="WT") for i in range(3)]
    assert _messages(records) == []


def test_missing_value_is_not_a_conflict():
    records = [
        _record("a.nwb", genotype=None, strain=""),
        _record("b.nwb", genotype="Dat-Cre", strain="C57BL/6J"),
        _record("c.nwb", genotype="Dat-Cre", strain=None),
    ]
    assert _messages(records) == []


def test_date_of_birth():
    same = [_record("a.nwb", date_of_birth="2023-10-24T00:00:00-07:00") for _ in range(2)]
    assert _messages(same) == []
    different = [
        _record("a.nwb", date_of_birth="2023-01-10T00:00:00-07:00"),
        _record("b.nwb", date_of_birth="2024-01-10T00:00:00-07:00"),
    ]
    assert len(_messages(different)) == 1


def test_different_subject_ids_are_not_compared():
    assert _messages([_record("a.nwb", subject_id="1", sex="M"), _record("b.nwb", subject_id="2", sex="F")]) == []


def test_files_without_subject_are_skipped():
    assert _messages([_record("a.nwb", subject_id=None, sex="M"), _record("b.nwb", subject_id=None, sex="F")]) == []


def _write_nwbfile(path: Path, identifier: str, subject: Subject) -> None:
    nwbfile = NWBFile(
        session_description="",
        identifier=identifier,
        session_start_time=datetime(2024, 1, 1, tzinfo=timezone.utc),
        subject=subject,
    )
    with NWBHDF5IO(path=str(path), mode="w") as io:
        io.write(nwbfile)


@pytest.fixture
def folder_with_conflict(tmp_path):
    date_of_birth = datetime(2023, 10, 1, tzinfo=timezone.utc)
    _write_nwbfile(
        tmp_path / "ses1.nwb",
        identifier="1",
        subject=Subject(
            subject_id="mouse1",
            species="Mus musculus",
            sex="M",
            genotype="WT",
            age="P60D",
            date_of_birth=date_of_birth,
        ),
    )
    _write_nwbfile(
        tmp_path / "ses2.nwb",
        identifier="2",
        subject=Subject(
            subject_id="mouse1",
            species="Mus musculus",
            sex="M",
            genotype="Dat-Cre",
            age="P70D",
            date_of_birth=date_of_birth,
        ),
    )
    return tmp_path


def test_inspect_all_reports_conflict(folder_with_conflict):
    messages = [
        m
        for m in inspect_all(path=folder_with_conflict, skip_validate=True, progress_bar=False)
        if m.check_function_name == "check_subject_consistency_across_files"
    ]
    assert len(messages) == 1
    assert "genotype:" in messages[0].message
    assert "sex:" not in messages[0].message and "date_of_birth:" not in messages[0].message


def test_inspect_all_respects_ignore_and_config(folder_with_conflict):
    name = "check_subject_consistency_across_files"
    ignored = list(inspect_all(path=folder_with_conflict, skip_validate=True, progress_bar=False, ignore=[name]))
    assert not any(m.check_function_name == name for m in ignored)

    skipped = list(
        inspect_all(path=folder_with_conflict, skip_validate=True, progress_bar=False, config=dict(SKIP=[name]))
    )
    assert not any(m.check_function_name == name for m in skipped)

    lowered = [
        m
        for m in inspect_all(
            path=folder_with_conflict,
            skip_validate=True,
            progress_bar=False,
            config=dict(BEST_PRACTICE_SUGGESTION=[name]),
        )
        if m.check_function_name == name
    ]
    assert len(lowered) == 1 and lowered[0].importance == Importance.BEST_PRACTICE_SUGGESTION

    above_threshold = list(
        inspect_all(
            path=folder_with_conflict,
            skip_validate=True,
            progress_bar=False,
            config=dict(BEST_PRACTICE_SUGGESTION=[name]),
            importance_threshold="BEST_PRACTICE_VIOLATION",
        )
    )
    assert not any(m.check_function_name == name for m in above_threshold)
