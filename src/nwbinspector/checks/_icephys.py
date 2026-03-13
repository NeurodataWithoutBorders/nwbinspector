"""Checks specific to intracellular electrophysiology neurodata types."""

from typing import Optional

from pynwb.icephys import IntracellularElectrode, SweepTable

from ._common import MOUSE_SPECIES_VALUES
from .._internal_configs._allen_ccf import get_allen_ccf_location_terms
from .._registration import Importance, InspectorMessage, register_check


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=IntracellularElectrode)
def check_intracellular_electrode_cell_id_exists(
    intracellular_electrode: IntracellularElectrode,
) -> Optional[InspectorMessage]:
    """
    Check if the IntracellularElectrode contains a cell_id.

    Best Practice: TODO
    """
    if hasattr(intracellular_electrode, "cell_id") and intracellular_electrode.cell_id is None:
        return InspectorMessage(message="Please include a unique cell_id associated with this IntracellularElectrode.")

    return None


@register_check(
    importance=Importance.BEST_PRACTICE_VIOLATION,
    neurodata_type=SweepTable,
    nwb_schema_version_gt="2.3.0",
)
def check_sweeptable_deprecated(sweep_table: SweepTable) -> Optional[InspectorMessage]:
    """
    Check if the deprecated SweepTable is used in an NWB file with schema version >= 2.4.0.

    Best Practice: SweepTable was deprecated in NWB 2.4.0 in favor of IntracellularRecordingsTable.
    """
    return InspectorMessage(
        message=(
            "SweepTable is deprecated in NWB schema version >= 2.4.0. "
            "Use IntracellularRecordingsTable instead. "
            "See NWBFile.add_intracellular_recordings for more information."
        )
    )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=IntracellularElectrode)
def check_intracellular_electrode_location_allen_ccf(
    intracellular_electrode: IntracellularElectrode,
) -> Optional[InspectorMessage]:
    """
    Check that the IntracellularElectrode location is a term in the Allen Mouse Brain CCF ontology.

    Only applies when the subject species is mouse.

    Best Practice: :ref:`best_practice_icephys_location`
    """
    nwbfile = intracellular_electrode.get_ancestor("NWBFile")
    if nwbfile is None or nwbfile.subject is None:
        return None
    species = nwbfile.subject.species
    if species not in MOUSE_SPECIES_VALUES:
        return None

    location = getattr(intracellular_electrode, "location", None)
    if location is None:
        return None

    valid_terms = get_allen_ccf_location_terms()
    if location not in valid_terms:
        return InspectorMessage(
            message=(
                f"IntracellularElectrode location '{location}' is not a term in the Allen Mouse Brain CCF ontology. "
                "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
                "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
                "terms do not meet your needs."
            )
        )

    return None
