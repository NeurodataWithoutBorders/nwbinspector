from datetime import datetime, timezone
from pathlib import Path

import pytest
from pynwb import NWBHDF5IO, NWBFile
from pynwb.file import Subject

from nwbinspector import Importance, inspect_all
from nwbinspector.checks._subject_consistency import (
    SubjectRecord,
    check_subject_consistency_across_files,
    compare_subjects,
    normalize_genotype,
    normalize_sex,
    normalize_species,
    normalize_strain,
)


def _record(path, subject_id="mouse1", **kwargs):
    return SubjectRecord(file_path=path, subject_id=subject_id, **kwargs)


def _messages(records):
    return list(check_subject_consistency_across_files(records))


@pytest.mark.parametrize("a,b", [("M", "male"), ("F", "Female"), ("f", "F")])
def test_sex_spellings_are_equal(a, b):
    assert normalize_sex(a) == normalize_sex(b)


def test_unknown_sex_is_missing():
    assert normalize_sex("U") is None


@pytest.mark.parametrize(
    "a,b",
    [
        ("Mus musculus", "mouse"),
        ("Mus musculus - House mouse", "Mus musculus"),
        ("http://purl.obolibrary.org/obo/NCBITaxon_10090", "Mus musculus"),
        ("Rattus norvegicus", "Rat"),
        ("Danio rerio", "zebrafish"),
    ],
)
def test_species_spellings_are_equal(a, b):
    assert normalize_species(a) == normalize_species(b)


def test_genotype_and_strain_spellings():
    assert normalize_genotype("Dat-Cre") == normalize_genotype("DAT_cre") == normalize_genotype("dat cre")
    assert normalize_genotype("WT") == normalize_genotype("wild-type")
    assert normalize_genotype("Fmr1 +/-") != normalize_genotype("Fmr1 -/-")
    assert normalize_strain("C57BL/6J") == normalize_strain("C57Bl6/J")
    assert normalize_strain("Wild Type") is None


def test_genotype_conflict():
    messages = _messages([_record("a.nwb", genotype="WT"), _record("b.nwb", genotype="Anxa1-flp")])
    assert len(messages) == 1
    assert "genotype: 'WT' in 1 file (a.nwb); 'Anxa1-flp' in 1 file (b.nwb)" in messages[0].message
    assert messages[0].importance == Importance.CRITICAL


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


def test_missing_value_is_not_a_conflict():
    assert _messages([_record("a.nwb", genotype=None, sex="U"), _record("b.nwb", genotype="Dat-Cre", sex="M")]) == []


def test_spelling_differences_are_not_conflicts():
    records = [_record("a.nwb", sex="M", species="mouse"), _record("b.nwb", sex="male", species="Mus musculus")]
    assert _messages(records) == []
    _, normalizations = compare_subjects(records)
    assert {n.field for n in normalizations} == {"sex", "species"}


def test_more_specific_strain_is_not_a_conflict():
    assert _messages([_record("a.nwb", strain="C57BL/6"), _record("b.nwb", strain="C57BL/6J")]) == []


def test_date_of_birth():
    same = [
        _record("a.nwb", date_of_birth="2023-10-24T00:00:00+02:00"),
        _record("b.nwb", date_of_birth="2023-10-23T22:00:00+00:00"),
    ]
    assert _messages(same) == []
    different = [_record("a.nwb", date_of_birth="2023-10-24"), _record("b.nwb", date_of_birth="2023-06-01")]
    assert len(_messages(different)) == 1
    placeholder = [_record("a.nwb", date_of_birth="1900-01-01"), _record("b.nwb", date_of_birth="2023-06-01")]
    assert _messages(placeholder) == []


def test_age_is_not_compared():
    assert _messages([_record("a.nwb", age="P60D"), _record("b.nwb", age="P90D")]) == []


def test_different_subject_ids_are_not_compared():
    assert _messages([_record("a.nwb", subject_id="1", sex="M"), _record("b.nwb", subject_id="2", sex="F")]) == []


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
    _write_nwbfile(
        tmp_path / "ses1.nwb",
        identifier="1",
        subject=Subject(subject_id="mouse1", species="Mus musculus", sex="M", genotype="WT", age="P60D"),
    )
    _write_nwbfile(
        tmp_path / "ses2.nwb",
        identifier="2",
        subject=Subject(subject_id="mouse1", species="mouse", sex="male", genotype="Dat-Cre", age="P70D"),
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
    assert "sex:" not in messages[0].message and "species:" not in messages[0].message


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
