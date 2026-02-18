"""Checks specific to intracellular electrophysiology neurodata types."""

from typing import Optional

from pynwb.icephys import IntracellularElectrode, SweepTable

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
