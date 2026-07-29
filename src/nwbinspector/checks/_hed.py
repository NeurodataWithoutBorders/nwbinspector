"""Check functions for HED (Hierarchical Event Descriptor) annotations added by the ``ndx-hed`` extension."""

from collections import defaultdict
from typing import Any, Iterable, Optional

from hdmf.common import DynamicTable, MeaningsTable
from pynwb import NWBFile

from .._registration import Importance, InspectorMessage, register_check

# The ndx-hed package is an optional dependency, installed with `pip install nwbinspector[hed]`.
# ImportError rather than ModuleNotFoundError is caught because releases of ndx-hed that predate its
# support for pynwb>=4.0 import packages that are not compatible with the rest of this environment.
try:
    from hed.errors import HedFileError
    from ndx_hed import HedLabMetaData
    from ndx_hed.utils.hed_nwb_validator import HedNWBValidator

    _HAS_NDX_HED = True
except ImportError:
    _HAS_NDX_HED = False

# Names of the neurodata types that the ndx-hed extension uses to store HED annotations in a table column.
# These are compared by name so that the annotations can be found even when the ndx-hed package is not
# installed, in which case PyNWB builds the classes on the fly from the specification cached in the file.
_HED_COLUMN_TYPE_NAMES = ("HedTags", "HedValueVector")

# The HedLabMetaData object always has this fixed name
_HED_LAB_META_DATA_NAME = "hed_schema"

_MAXIMUM_NUMBER_OF_LISTED_COLUMNS = 3


def _get_hed_columns_of_table(table: DynamicTable) -> list:
    """Return the columns of a table that hold HED annotations."""
    return [column for column in table.columns if type(column).__name__ in _HED_COLUMN_TYPE_NAMES]


def _get_hed_columns_of_file(nwbfile: NWBFile) -> list:
    """Return every column of every table in the file that holds HED annotations."""
    return [
        neurodata_object
        for neurodata_object in nwbfile.objects.values()
        if type(neurodata_object).__name__ in _HED_COLUMN_TYPE_NAMES
    ]


def _describe_column(column: Any) -> str:
    """Describe a HED column by its name and the name of the table that contains it."""
    if getattr(column, "parent", None) is None:
        return f"'{column.name}'"

    return f"'{column.name}' of table '{column.parent.name}'"


def _get_hed_lab_meta_data(nwbfile: Optional[NWBFile]) -> Optional["HedLabMetaData"]:
    """Return the object that declares the HED schema version of the file, if there is one."""
    if nwbfile is None:
        return None

    hed_lab_meta_data = nwbfile.lab_meta_data.get(_HED_LAB_META_DATA_NAME, None)

    return hed_lab_meta_data if isinstance(hed_lab_meta_data, HedLabMetaData) else None


def _group_key(issue: dict) -> tuple:
    """
    Identify the issues that should be reported together as a single message.

    A single mistake that is repeated down a column, such as the same misspelled tag on every row, is
    reported by the HED validator once per row. The offending tag is part of the key so that different
    mistakes in the same column are still reported separately.
    """
    source_tag = issue.get("source_tag", None)

    return (issue.get("ec_column", None), issue.get("code", None), str(source_tag) if source_tag is not None else None)


def _format_issue_message(issues: list[dict[str, Any]]) -> str:
    """Compose the message for a group of issues that share a column, an error code, and a tag."""
    first_issue = issues[0]
    column_name = first_issue.get("ec_column", None)
    row_index = first_issue.get("ec_row", None)
    error_code = first_issue.get("code", None)

    source = f" in column '{column_name}'" if column_name is not None else ""
    if row_index is not None:
        source += f", row {row_index}"
    if error_code is not None:
        source += f" ({error_code})"

    reported_message = " ".join(str(first_issue.get("message", "no message was reported")).split())
    if not reported_message.endswith("."):
        reported_message += "."

    message = f"HED validation error{source}: {reported_message}"
    if len(issues) > 1:
        message += f" This error occurs on {len(issues)} rows; only the first is reported."

    return message


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

    Every error reported by the HED validator becomes its own message, except that an error repeated
    down a column is reported once with the number of rows it affects.

    The columns of the table are validated one at a time, which is what the ``HedTags`` and
    ``HedValueVector`` annotations mean on their own. Validation of the annotation of a row as a whole,
    which combines the columns of that row and requires reading the entire table into memory, is not
    performed here.

    This check requires the ``ndx-hed`` package, which is installed with `pip install nwbinspector[hed]`.
    Without it, the HED annotations of a file are not validated.

    Best Practice: :ref:`best_practice_hed_annotations`
    """
    if not _HAS_NDX_HED:
        return None
    if not _get_hed_columns_of_table(table=table):
        return None

    hed_lab_meta_data = _get_hed_lab_meta_data(nwbfile=table.get_ancestor("NWBFile"))
    if hed_lab_meta_data is None:
        return None  # A file without the HED schema version is reported by check_hed_lab_metadata_exists

    try:
        issues = HedNWBValidator(hed_lab_meta_data).validate_table(table)
    except (HedFileError, ValueError) as exception:
        yield InspectorMessage(message=f"The HED annotations of this table could not be validated: {exception}")
        return None

    grouped_issues: dict = defaultdict(list)
    for issue in issues:
        grouped_issues[_group_key(issue=issue)].append(issue)

    for issues_in_group in grouped_issues.values():
        yield InspectorMessage(message=_format_issue_message(issues=issues_in_group))

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=MeaningsTable)
def check_hed_value_vector_not_in_meanings_table(meanings_table: MeaningsTable) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that a MeaningsTable does not store its HED annotations in a HedValueVector column.

    A MeaningsTable assigns a meaning to each individual value of a categorical column, so its HED
    annotations are complete HED strings in a ``HedTags`` column. A ``HedValueVector`` is a template
    with a ``#`` placeholder that a value from the column is substituted into, which has no role in a
    MeaningsTable.

    Best Practice: :ref:`best_practice_hed_value_vector_meanings_table`
    """
    for column in meanings_table.columns:
        if type(column).__name__ == "HedValueVector":
            yield InspectorMessage(
                message=(
                    f"Column '{column.name}' of MeaningsTable '{meanings_table.name}' is a HedValueVector, "
                    "which is not allowed in a MeaningsTable. A MeaningsTable assigns a HED annotation to "
                    "each individual value of a categorical column, so its annotations must be complete "
                    "HED strings stored in a HedTags column."
                )
            )

    return None
