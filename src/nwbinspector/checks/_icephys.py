"""Checks specific to intracellular electrophysiology neurodata types."""

from pathlib import Path
from typing import Optional

import h5py
from packaging.version import Version
from pynwb.icephys import IntracellularElectrode, SweepTable

from .._registration import Importance, InspectorMessage, register_check
from ..tools import get_nwbfile_path_from_internal_object


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


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=SweepTable)
def check_sweeptable_deprecated(sweep_table: SweepTable) -> Optional[InspectorMessage]:
    """
    Check if the deprecated SweepTable is used in an NWB file with schema version >= 2.4.0.

    Best Practice: SweepTable was deprecated in NWB 2.4.0 in favor of IntracellularRecordingsTable.
    """
    # Get the file path from the sweep_table object
    try:
        nwbfile_path_str = get_nwbfile_path_from_internal_object(sweep_table)
        if nwbfile_path_str is None:
            return None
        nwbfile_path = Path(nwbfile_path_str)
    except Exception:
        # If we can't get the file path, skip this check
        return None

    # Read the NWB version from the file
    try:
        with h5py.File(nwbfile_path, "r") as h5file:
            nwb_version_str = h5file.attrs.get("nwb_version")
            if nwb_version_str is None:
                # If no nwb_version attribute, skip this check
                return None
            # Handle both string and bytes
            if isinstance(nwb_version_str, bytes):
                nwb_version_str = nwb_version_str.decode("utf-8")
    except Exception:
        # If we can't read the file or the attribute, skip this check
        return None

    try:
        nwb_version = Version(nwb_version_str)
        deprecated_version = Version("2.4.0")
    except Exception:
        # If version parsing fails, skip this check
        return None

    if nwb_version >= deprecated_version:
        return InspectorMessage(
            message=(
                f"SweepTable is deprecated in NWB version {nwb_version_str}. "
                "Use IntracellularRecordingsTable instead. "
                "See NWBFile.add_intracellular_recordings for more information."
            )
        )

    return None
