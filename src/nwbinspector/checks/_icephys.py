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
    nwbfile_path = Path(get_nwbfile_path_from_internal_object(sweep_table))

    # Read the NWB version from the file
    with h5py.File(nwbfile_path, "r") as h5file:
        nwb_version_str = h5file.attrs["nwb_version"]
        # Handle both string and bytes
        if isinstance(nwb_version_str, bytes):
            nwb_version_str = nwb_version_str.decode("utf-8")

    nwb_version = Version(nwb_version_str)
    deprecated_version = Version("2.4.0")

    if nwb_version >= deprecated_version:
        return InspectorMessage(
            message=(
                f"SweepTable is deprecated in NWB version {nwb_version_str}. "
                "Use IntracellularRecordingsTable instead. "
                "See NWBFile.add_intracellular_recordings for more information."
            )
        )

    return None
