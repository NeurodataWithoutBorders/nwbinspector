"""
Checks that compare the Subject metadata of several NWB files.

These run once over all files of a folder (see ``inspect_all``) rather than on one object of one file, so they are
not in the registry of per-object checks.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Iterable, Optional

from .._registration import Importance, InspectorMessage

COMPARED_FIELDS = ("species", "sex", "genotype", "strain", "date_of_birth")

N_EXAMPLES = 4


@dataclass
class SubjectRecord:
    """The Subject fields of one file that are compared across files, as stored."""

    file_path: str
    subject_id: Optional[str]
    species: Optional[str] = None
    sex: Optional[str] = None
    genotype: Optional[str] = None
    strain: Optional[str] = None
    date_of_birth: Optional[str] = None

    @classmethod
    def from_nwbfile(cls, nwbfile: Any, file_path: str) -> "SubjectRecord":
        subject = nwbfile.subject
        if subject is None:
            return cls(file_path=str(file_path), subject_id=None)
        date_of_birth = subject.date_of_birth
        return cls(
            file_path=str(file_path),
            subject_id=subject.subject_id,
            species=subject.species,
            sex=subject.sex,
            genotype=subject.genotype,
            strain=subject.strain,
            date_of_birth=date_of_birth.isoformat() if date_of_birth is not None else None,
        )


def _fmt_files(paths: list[str]) -> str:
    names = [p.rsplit("/", 1)[-1] for p in paths]
    shown = ", ".join(names[:N_EXAMPLES])
    return f"{len(names)} file{'s' if len(names) != 1 else ''} ({shown}{', ...' if len(names) > N_EXAMPLES else ''})"


def find_subject_conflicts(records: Iterable[SubjectRecord]) -> dict[str, dict[str, dict[str, list[str]]]]:
    """
    Find the fields whose values differ between the files of each subject_id.

    Returns {subject_id: {field: {value: [file paths]}}}, holding only the fields with more than one value.
    Values are compared as stored. A field that is not set (None or an empty string) in a file is left out
    for that file, so a value that is missing in some files and set in others is not a conflict.
    """
    by_subject: dict[str, list[SubjectRecord]] = defaultdict(list)
    for record in records:
        if record.subject_id:
            by_subject[record.subject_id].append(record)

    conflicts: dict[str, dict[str, dict[str, list[str]]]] = {}
    for subject_id, subject_records in sorted(by_subject.items()):
        if len(subject_records) < 2:
            continue
        for field_name in COMPARED_FIELDS:
            files_by_value: dict[str, list[str]] = defaultdict(list)
            for record in subject_records:
                value = getattr(record, field_name)
                if value is None or value == "":
                    continue
                files_by_value[value].append(record.file_path)
            if len(files_by_value) > 1:
                conflicts.setdefault(subject_id, {})[field_name] = {
                    value: sorted(paths) for value, paths in files_by_value.items()
                }
    return conflicts


def check_subject_consistency_across_files(records: Iterable[SubjectRecord]) -> Iterable[InspectorMessage]:
    """
    Report each subject_id whose species, sex, genotype, strain or date_of_birth differ across files.

    One message per subject, listing every field in conflict with the files that hold each value. Values are
    compared as stored, and a value that is missing in some files is not a conflict.
    """
    for subject_id, fields in find_subject_conflicts(records).items():
        parts: list[str] = []
        all_paths: list[str] = []
        for field_name, files_by_value in fields.items():
            listed = "; ".join(f"'{value}' in {_fmt_files(paths)}" for value, paths in files_by_value.items())
            parts.append(f"{field_name}: {listed}.")
            all_paths.extend(path for paths in files_by_value.values() for path in paths)
        yield InspectorMessage(
            message=(
                f"Subject '{subject_id}' has conflicting metadata across files. "
                + " ".join(parts)
                + " A subject's species, sex, genotype, strain and date of birth should be the same in every "
                "file; if these are different animals, give them different subject_ids."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_subject_consistency_across_files",
            object_type="Subject",
            object_name="subject",
            location="/general/subject",
            file_path=min(all_paths),
        )


check_subject_consistency_across_files.importance = Importance.CRITICAL  # type: ignore[attr-defined]
