"""Check functions for HED (Hierarchical Event Descriptor) annotations added by the ``ndx-hed`` extension."""

import re
from collections import defaultdict
from typing import Any, Iterable, Optional

from hdmf.common import DynamicTable, MeaningsTable
from pynwb import NWBFile

from .._registration import Importance, InspectorMessage, register_check

# The ndx-hed package is an optional dependency, installed with `pip install nwbinspector[hed]`. HedDurationVector
# is imported because it was added in the first release that supports pynwb>=4.0 and validates a table without
# reading the tables that carry no HED, so older releases are treated as not installed.
try:
    from hed.errors import ErrorHandler, ErrorSeverity, HedFileError
    from ndx_hed import HedDurationVector, HedLabMetaData  # noqa: F401
    from ndx_hed.utils.hed_nwb_validator import HedNWBValidator

    _HAS_NDX_HED = True
except ImportError:
    _HAS_NDX_HED = False

# Names of the neurodata types that the ndx-hed extension uses to store HED annotations in a table column.
# These are compared by name so that the annotations can be found even when the ndx-hed package is not
# installed, in which case PyNWB builds the classes on the fly from the specification cached in the file.
_HED_COLUMN_TYPE_NAMES = ("HedTags", "HedValueVector", "HedDurationVector")

# The HedLabMetaData object always has this fixed name
_HED_LAB_META_DATA_NAME = "hed_schema"

# Reported by check_meanings_table_includes_all_values for every MeaningsTable, with or without HED
_WARNING_CODES_REPORTED_ELSEWHERE = ("SIDECAR_KEY_MISSING",)

_MAXIMUM_NUMBER_OF_LISTED_COLUMNS = 3
_MAXIMUM_NUMBER_OF_LISTED_VALUES = 5

# hedtools ends many messages with the character span of the problem, which is not useful without the string
_CHARACTER_SPAN_PATTERN = re.compile(r"\s*Problem spans string indexes: \d+, \d+\s*$")


def _is_hed_column(column: Any) -> bool:
    return type(column).__name__ in _HED_COLUMN_TYPE_NAMES


def _table_has_hed(table: DynamicTable) -> bool:
    """Return True if a table has a HED column of its own or in one of the MeaningsTables of its columns."""
    owners = [table, *getattr(table, "meanings_tables", {}).values()]

    return any(_is_hed_column(column=column) for owner in owners for column in owner.columns)


def _get_hed_columns_of_file(nwbfile: NWBFile) -> list:
    """Return every column of every table in the file, MeaningsTables included, that holds HED annotations."""
    return [neurodata_object for neurodata_object in nwbfile.objects.values() if _is_hed_column(neurodata_object)]


def _describe_column(column: Any) -> str:
    """Describe a HED column by its name and the name of the table that contains it."""
    if getattr(column, "parent", None) is None:
        return f"'{column.name}'"

    return f"'{column.name}' of table '{column.parent.name}'"


def _validate_table(table: DynamicTable, check_for_warnings: bool, assemble: bool) -> Optional[list[dict]]:
    """
    Run the ndx-hed validator on a table, or return None if the table has nothing that can be validated.

    The validator reads only the tables that carry HED. With ``assemble=True`` it reads the whole of such a
    table, to validate the HED of each row as a whole, but only after the HED of each column has passed.
    """
    if isinstance(table, MeaningsTable):
        return None  # Validated as part of the table whose column it annotates
    if not _table_has_hed(table=table):
        return None

    nwbfile = table.get_ancestor("NWBFile")
    hed_lab_meta_data = None if nwbfile is None else nwbfile.lab_meta_data.get(_HED_LAB_META_DATA_NAME, None)
    if not isinstance(hed_lab_meta_data, HedLabMetaData):
        return None  # A file without the HED schema version is reported by check_hed_lab_metadata_exists

    error_handler = ErrorHandler(check_for_warnings=check_for_warnings)

    return HedNWBValidator(hed_lab_meta_data).validate_table(table, error_handler=error_handler, assemble=assemble)


def _describe_location(issue: dict[str, Any], include_row: bool) -> str:
    """Describe where in the table the HED of an issue comes from."""
    column_name = issue.get("ec_column", None)
    row_index = issue.get("ec_row", None) if include_row else None
    sidecar_column_name = issue.get("ec_sidecarColumnName", None)
    sidecar_key_name = issue.get("ec_sidecarKeyName", None)

    if sidecar_column_name is not None and sidecar_key_name is not None:
        return f" in the HED of value '{sidecar_key_name}' in the MeaningsTable of column '{sidecar_column_name}'"
    if sidecar_column_name is not None:
        return f" in the HED of column '{sidecar_column_name}'"
    if column_name is not None and row_index is not None:
        return f" in column '{column_name}' at row index {row_index}"
    if column_name is not None:
        return f" in column '{column_name}'"
    if row_index is not None:
        assembled = issue.get("ec_HedString", None)
        assembled_text = f" ('{assembled}')" if assembled else ""
        return f" in the combined HED of row index {row_index}{assembled_text}"
    if issue.get("ec_row", None) is not None:
        return " in the combined HED of rows"

    return ""


def _group_key(issue: dict[str, Any]) -> tuple:
    """
    Identify the issues that are reported together as a single message.

    The validator reports each distinct value of a column once, with the number of rows holding it, so a
    mistake in a column of free values, such as a word where a number is expected, is still reported once per
    value. Issues with the same code in the same column, or of the same MeaningsTable value, are therefore
    reported as one message that lists the HED strings, as are issues with the same code in the combined HED
    of different rows.
    """
    return (
        issue.get("code", None),
        issue.get("ec_column", None),
        issue.get("ec_sidecarColumnName", None),
        issue.get("ec_sidecarKeyName", None),
        issue.get("ec_row", None) is None,
    )


def _describe_occurrence(issue: dict[str, Any]) -> str:
    """Describe a HED string with an issue by the first row that holds it and the number of rows that do."""
    hed_string = issue.get("ec_HedString", issue.get("source_tag", None))
    number_of_rows = int(issue.get("row_count", 1))
    rows_text = f", {number_of_rows} rows" if number_of_rows > 1 else ""

    return f"'{hed_string}' (row index {issue['ec_row']}{rows_text})"


def _format_issues(issues: list[dict[str, Any]], kind: str) -> str:
    """
    Compose the message for a group of issues that share a code and a location.

    The message of the first issue is shown. When the group holds more than one issue, the HED strings that
    have the issue are listed, so that every value to fix is named without a message for each.
    """
    first_issue = issues[0]
    code = first_issue.get("code", None)
    code_text = f" {code}" if code is not None else ""

    reported_message = " ".join(str(first_issue.get("message", "no message was reported")).split())
    reported_message = _CHARACTER_SPAN_PATTERN.sub("", reported_message)
    if not reported_message.endswith("."):
        reported_message += "."

    location = _describe_location(issue=first_issue, include_row=len(issues) == 1)
    message = f"HED {kind}{code_text}{location}: {reported_message}"

    if first_issue.get("ec_row", None) is None:
        return message
    if len(issues) == 1:
        number_of_rows = int(first_issue.get("row_count", 1))
        if number_of_rows > 1:
            message += f" The same HED string occurs on {number_of_rows} rows."
        return message

    listed_issues = issues[:_MAXIMUM_NUMBER_OF_LISTED_VALUES]
    occurrences_text = ", ".join(_describe_occurrence(issue=issue) for issue in listed_issues)
    if len(issues) > len(listed_issues):
        occurrences_text += f" (and {len(issues) - len(listed_issues)} more)"

    if first_issue.get("ec_column", None) is None:  # The combined HED of a row is validated row by row
        return f"{message} {len(issues)} rows have this {kind}: {occurrences_text}."

    number_of_rows = sum(int(issue.get("row_count", 1)) for issue in issues)
    return (
        f"{message} {len(issues)} different HED strings on {number_of_rows} rows have this {kind}: "
        f"{occurrences_text}."
    )


def _yield_grouped_messages(issues: list[dict[str, Any]], kind: str) -> Iterable[InspectorMessage]:
    grouped_issues: dict = defaultdict(list)
    for issue in issues:
        grouped_issues[_group_key(issue=issue)].append(issue)

    for issues_in_group in grouped_issues.values():
        yield InspectorMessage(message=_format_issues(issues=issues_in_group, kind=kind))


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBFile)
def check_hed_lab_metadata_exists(nwbfile: NWBFile) -> Optional[InspectorMessage]:
    """
    Check that a file containing HED annotations also declares the HED schema version they use.

    Best Practice: :ref:`best_practice_hed_lab_metadata`
    """
    hed_columns = _get_hed_columns_of_file(nwbfile=nwbfile)
    if not hed_columns:
        return None
    if nwbfile.lab_meta_data.get(_HED_LAB_META_DATA_NAME, None) is not None:
        return None

    # Sorted so that the message does not depend on the order in which the objects happen to be traversed
    described_columns = sorted(_describe_column(column=column) for column in hed_columns)
    listed_columns = described_columns[:_MAXIMUM_NUMBER_OF_LISTED_COLUMNS]
    number_of_unlisted_columns = len(described_columns) - len(listed_columns)
    columns_text = ", ".join(listed_columns)
    if number_of_unlisted_columns > 0:
        columns_text += f" (and {number_of_unlisted_columns} more)"

    return InspectorMessage(
        message=(
            f"This file contains HED annotations in column {columns_text}, but it does not contain a "
            "HedLabMetaData object declaring the version of the HED schema that those annotations use. "
            "Without it the annotations cannot be interpreted or validated. Add one with, for example, "
            "`nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version='8.4.0'))`."
        )
    )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DynamicTable)
def check_hed_annotations_valid(table: DynamicTable) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that the HED annotations of a table are valid against the HED schema declared by the file.

    The table is validated by ``ndx-hed``, which covers its ``HedTags``, ``HedValueVector``, and
    ``HedDurationVector`` columns and the HED of the MeaningsTables of its columns. Once those pass, the HED of
    each row is assembled from all of them and validated as a whole, which catches errors such as a tag
    repeated in two columns. Tables without HED are not read. Assembling the rows reads the whole table, which
    for a table of 100,000 rows takes several seconds.

    The validator works in stages and stops at the first stage that finds errors, so fixing the reported errors
    can reveal further ones on the next run.

    Errors with the same code in the same place, such as words in a column of numbers, are reported as one
    message that lists the HED strings with the error.

    This check requires the ``ndx-hed`` package, which is installed with `pip install nwbinspector[hed]`.

    Best Practice: :ref:`best_practice_hed_annotations`
    """
    if not _HAS_NDX_HED:
        if not isinstance(table, MeaningsTable) and _table_has_hed(table=table):
            yield InspectorMessage(
                message=(
                    "This table contains HED annotations, but they were not validated because the 'ndx-hed' "
                    "package is not installed. Install it with `pip install nwbinspector[hed]`."
                )
            )
        return None

    try:
        issues = _validate_table(table=table, check_for_warnings=False, assemble=True)
    except HedFileError as exception:
        yield InspectorMessage(message=f"The HED annotations of this table could not be validated: {exception}")
        return None

    yield from _yield_grouped_messages(issues=issues or [], kind="error")

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DynamicTable)
def check_hed_annotations_warnings(table: DynamicTable) -> Optional[Iterable[InspectorMessage]]:
    """
    Report the warnings of the HED validator for the annotations of a table, such as an extended tag.

    The HED of each row is not assembled for this check, so warnings that only arise from the combined HED of
    a row are not reported. A value of a categorical column that is missing from its MeaningsTable is reported
    by ``check_meanings_table_includes_all_values`` instead.

    This check requires the ``ndx-hed`` package, which is installed with `pip install nwbinspector[hed]`.

    Best Practice: :ref:`best_practice_hed_extensions`
    """
    if not _HAS_NDX_HED:
        return None

    try:
        issues = _validate_table(table=table, check_for_warnings=True, assemble=False)
    except HedFileError:
        return None  # Reported by check_hed_annotations_valid

    warnings = [
        issue
        for issue in issues or []
        if issue.get("severity", None) == ErrorSeverity.WARNING
        and issue.get("code", None) not in _WARNING_CODES_REPORTED_ELSEWHERE
    ]
    yield from _yield_grouped_messages(issues=warnings, kind="warning")

    return None
