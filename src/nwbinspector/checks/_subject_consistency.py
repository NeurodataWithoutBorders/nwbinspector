"""
Checks that compare the Subject metadata of several NWB files.

These run once over all files of a folder (see ``inspect_all``) rather than on one object of one file, so they are
not in the registry of per-object checks.
"""

from __future__ import annotations

import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional

from .._registration import Importance, InspectorMessage

COMPARED_FIELDS = ("species", "sex", "genotype", "strain", "date_of_birth")

# Values that mean "not given". Compared after lowercasing and stripping.
MISSING_VALUES = {
    "",
    "none",
    "null",
    "nan",
    "n/a",
    "na",
    "unknown",
    "unk",
    "not specified",
    "not available",
    "unspecified",
    "[]",
    "?",
    "-",
}
# Placeholder birth dates seen in conversions; treated as missing.
PLACEHOLDER_BIRTH_DATES = {dt.date(1900, 1, 1), dt.date(1970, 1, 1), dt.date(1, 1, 1)}
# Two birth dates within this many days are the same date (time zone and midnight conventions).
BIRTH_DATE_TOLERANCE_DAYS = 1

N_EXAMPLES = 4

# --------------------------------------------------------------------------- normalization

_SEX = {
    "m": "M",
    "male": "M",
    "f": "F",
    "female": "F",
    "o": "O",
    "other": "O",
    "u": None,
    "unknown": None,
}

# Common and Latin names, NCBI taxonomy ids, for the species seen on DANDI.
_SPECIES_ALIASES = {
    "Mus musculus": ["mus musculus", "mouse", "mice", "house mouse", "ncbitaxon_10090", "ncbitaxon:10090", "10090"],
    "Rattus norvegicus": ["rattus norvegicus", "rat", "rats", "norway rat", "brown rat", "ncbitaxon_10116", "10116"],
    "Homo sapiens": ["homo sapiens", "human", "humans", "ncbitaxon_9606", "9606"],
    "Macaca mulatta": ["macaca mulatta", "rhesus macaque", "rhesus monkey", "rhesus", "ncbitaxon_9544", "9544"],
    "Macaca fascicularis": ["macaca fascicularis", "cynomolgus monkey", "crab-eating macaque", "ncbitaxon_9541"],
    "Macaca nemestrina": ["macaca nemestrina", "pig-tailed macaque", "pigtail macaque", "ncbitaxon_9545"],
    "Callithrix jacchus": ["callithrix jacchus", "common marmoset", "marmoset", "ncbitaxon_9483"],
    "Danio rerio": ["danio rerio", "zebrafish", "ncbitaxon_7955", "7955"],
    "Danionella cerebrum": ["danionella cerebrum", "danionella translucida", "danionella"],
    "Drosophila melanogaster": ["drosophila melanogaster", "fruit fly", "drosophila", "ncbitaxon_7227"],
    "Caenorhabditis elegans": ["caenorhabditis elegans", "c. elegans", "c elegans", "ncbitaxon_6239"],
    "Mustela putorius furo": ["mustela putorius furo", "ferret", "ncbitaxon_9669"],
    "Felis catus": ["felis catus", "cat", "domestic cat", "ncbitaxon_9685"],
    "Sus scrofa": ["sus scrofa", "pig", "swine", "ncbitaxon_9823"],
    "Taeniopygia guttata": ["taeniopygia guttata", "zebra finch", "ncbitaxon_59729"],
    "Meriones unguiculatus": ["meriones unguiculatus", "mongolian gerbil", "gerbil", "ncbitaxon_10047"],
}
_SPECIES_LOOKUP = {alias: canonical for canonical, aliases in _SPECIES_ALIASES.items() for alias in aliases}

_WT_SYNONYMS = {"wt", "wild type", "wildtype", "wild-type", "+/+", "wt/wt", "c57bl/6j wt", "wild"}


def _clean(value: Any) -> Optional[str]:
    """Decode, strip and collapse whitespace; return None for empty or placeholder values."""
    if value is None:
        return None
    if isinstance(value, bytes):
        value = value.decode("utf-8", errors="replace")
    if not isinstance(value, str):
        value = str(value)
    value = " ".join(value.split())
    if value.lower() in MISSING_VALUES:
        return None
    return value


def normalize_sex(value: Any) -> Optional[str]:
    value = _clean(value)
    if value is None:
        return None
    return _SEX.get(value.lower(), value.upper())


def normalize_species(value: Any) -> Optional[str]:
    value = _clean(value)
    if value is None:
        return None
    low = value.lower()
    # DANDI-style "Mus musculus - House mouse" and ontology URLs.
    candidates = [low] + [part.strip() for part in re.split(r"\s+-\s+|[/#()]", low) if part.strip()]
    for cand in candidates:
        if cand in _SPECIES_LOOKUP:
            return _SPECIES_LOOKUP[cand]
    # Fall back to a binomial-looking prefix: "Mus musculus C57BL/6" stays comparable to "Mus musculus".
    match = re.match(r"^([a-z]+ [a-z]+)\b", low)
    if match and match.group(1) in _SPECIES_LOOKUP:
        return _SPECIES_LOOKUP[match.group(1)]
    return low


def _token_key(value: str) -> str:
    """Case, spacing and separator-insensitive form of a genotype or strain string."""
    low = value.lower()
    low = re.sub(r"[\s_\-.,;:]+", "", low)  # Dat-Cre, DAT_cre, dat cre -> datcre
    return low


def normalize_genotype(value: Any) -> Optional[str]:
    value = _clean(value)
    if value is None:
        return None
    if value.lower() in _WT_SYNONYMS:
        return "wt"
    return _token_key(value)


def normalize_strain(value: Any) -> Optional[str]:
    value = _clean(value)
    if value is None:
        return None
    if value.lower() in _WT_SYNONYMS:
        return None  # the best practice recommends "Wild Type" when no specific strain is used
    return _token_key(value).replace("/", "")  # C57BL/6J, C57Bl6/J, c57bl6j -> c57bl6j


def parse_datetime(value: Any) -> Optional[dt.datetime]:
    value = _clean(value)
    if value is None:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            return dt.datetime.combine(dt.date.fromisoformat(value[:10]), dt.time())
        except ValueError:
            return None


def normalize_date_of_birth(value: Any) -> Optional[dt.date]:
    parsed = parse_datetime(value)
    if parsed is None:
        return None
    if parsed.date() in PLACEHOLDER_BIRTH_DATES:
        return None
    return parsed.date()


NORMALIZERS = {
    "species": normalize_species,
    "sex": normalize_sex,
    "genotype": normalize_genotype,
    "strain": normalize_strain,
    "date_of_birth": normalize_date_of_birth,
}


# --------------------------------------------------------------------------- reading


@dataclass
class SubjectRecord:
    """The Subject fields of one file, as stored (raw strings)."""

    file_path: str
    subject_id: Optional[str]
    species: Optional[str] = None
    sex: Optional[str] = None
    genotype: Optional[str] = None
    strain: Optional[str] = None
    date_of_birth: Optional[str] = None
    age: Optional[str] = None
    age_reference: Optional[str] = None
    session_start_time: Optional[str] = None
    extra: dict = field(default_factory=dict)

    @classmethod
    def from_nwbfile(cls, nwbfile: Any, file_path: str) -> "SubjectRecord":
        subject = nwbfile.subject
        if subject is None:
            return cls(file_path=str(file_path), subject_id=None)
        dob = subject.date_of_birth
        return cls(
            file_path=str(file_path),
            subject_id=_clean(subject.subject_id),
            species=subject.species,
            sex=subject.sex,
            genotype=subject.genotype,
            strain=subject.strain,
            date_of_birth=dob.isoformat() if dob is not None else None,
            age=subject.age,
            age_reference=getattr(subject, "age__reference", None),
            session_start_time=nwbfile.session_start_time.isoformat(),
        )


# --------------------------------------------------------------------------- comparison


def _same(field_name: str, a: Any, b: Any) -> bool:
    if field_name == "date_of_birth":
        return abs((a - b).days) <= BIRTH_DATE_TOLERANCE_DAYS
    return a == b


def _group_values(field_name: str, records: list[SubjectRecord]) -> tuple[dict, dict]:
    """
    Group the files of one subject by normalized value of one field.

    Returns (groups, raw_forms): groups maps a representative normalized value to the files holding a
    value equal to it, raw_forms maps it to the distinct raw spellings seen (for reporting normalizations).
    Files where the field is empty are left out.
    """
    groups: dict = {}
    raw_forms: dict = defaultdict(set)
    for rec in records:
        raw = getattr(rec, field_name)
        norm = NORMALIZERS[field_name](raw)
        if norm is None:
            continue
        key = next((k for k in groups if _same(field_name, k, norm)), norm)
        groups.setdefault(key, []).append(rec.file_path)
        raw_forms[key].add(_clean(raw))
    return groups, raw_forms


def _is_refinement(field_name: str, values: list) -> bool:
    """
    True when, for strain or genotype, every value is contained in the longest one (C57BL6 within
    C57BL6J, datcre within datcre;ai14 normalized as datcreai14). Such values add detail rather than
    contradict, so they are not reported as a conflict.
    """
    if field_name not in ("strain", "genotype") or len(values) < 2:
        return False
    longest = max(values, key=len)
    return all(v in longest for v in values)


@dataclass
class FieldConflict:
    subject_id: str
    field: str
    values: dict  # raw spelling(s) -> list of files
    refinement: bool = False


@dataclass
class Normalization:
    subject_id: str
    field: str
    spellings: list  # raw spellings treated as one value


def compare_subjects(
    records: Iterable[SubjectRecord], fields: Iterable[str] = COMPARED_FIELDS
) -> tuple[list[FieldConflict], list[Normalization]]:
    """Return (conflicts, normalizations) over all subject_ids present in more than one file."""
    by_subject: dict[str, list[SubjectRecord]] = defaultdict(list)
    for rec in records:
        if rec.subject_id is not None:
            by_subject[rec.subject_id].append(rec)
    conflicts: list[FieldConflict] = []
    normalizations: list[Normalization] = []
    for subject_id, recs in sorted(by_subject.items()):
        if len(recs) < 2:
            continue
        for field_name in fields:
            groups, raw_forms = _group_values(field_name, recs)
            for key, forms in raw_forms.items():
                if len(forms) > 1:
                    normalizations.append(Normalization(subject_id, field_name, sorted(forms)))
            if len(groups) > 1:
                values = {" | ".join(sorted(raw_forms[k])): sorted(paths) for k, paths in groups.items()}
                refinement = _is_refinement(field_name, [str(k) for k in groups])
                conflicts.append(FieldConflict(subject_id, field_name, values, refinement))
    return conflicts, normalizations


def _fmt_files(paths: list[str]) -> str:
    names = [p.rsplit("/", 1)[-1] for p in paths]
    shown = ", ".join(names[:N_EXAMPLES])
    return f"{len(names)} file{'s' if len(names) != 1 else ''} ({shown}{', ...' if len(names) > N_EXAMPLES else ''})"


def check_subject_consistency_across_files(records: Iterable[SubjectRecord]) -> Iterable[InspectorMessage]:
    """
    Report each subject_id whose species, sex, genotype, strain or date_of_birth disagree across files.

    One message per subject, listing every field in conflict with the files that hold each value.
    Values that differ only in form (M and male, mouse and Mus musculus, Dat-Cre and DAT_cre) are
    treated as equal; strain or genotype values that only add detail (C57BL/6 and C57BL/6J) are not
    reported; empty values are ignored.
    """
    conflicts, _ = compare_subjects(records)
    by_subject = defaultdict(list)
    for c in conflicts:
        if not c.refinement:
            by_subject[c.subject_id].append(c)
    for subject_id, items in by_subject.items():
        parts = []
        first_file = None
        for c in items:
            listed = "; ".join(f"'{value}' in {_fmt_files(paths)}" for value, paths in c.values.items())
            parts.append(f"{c.field}: {listed}")
            first_file = first_file or sorted(p for ps in c.values.values() for p in ps)[0]
        yield InspectorMessage(
            message=(
                f"Subject '{subject_id}' has conflicting metadata across files. "
                + " ".join(f"{p}." for p in parts)
                + " A subject's species, sex, genotype, strain and date of birth should be the same in every "
                "file; if these are different animals, give them different subject_ids."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_subject_consistency_across_files",
            object_type="Subject",
            object_name="subject",
            location="/general/subject",
            file_path=first_file,
        )


check_subject_consistency_across_files.importance = Importance.CRITICAL  # type: ignore[attr-defined]
