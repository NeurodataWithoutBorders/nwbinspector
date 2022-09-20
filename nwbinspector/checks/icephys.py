from pynwb.icephys import IntracellularElectrode

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=IntracellularElectrode)
def check_intracellular_electrode_cell_id_exists(intracellular_electrode: IntracellularElectrode):
    """Check if the IntracellularElectrode contains a cell_id."""
    if getattr(intracellular_electrode, "cell_id", "") is None:  # Will only be None with PyNWB>=2.1.0
        return InspectorMessage(message="Please include a unique cell_id associated with this IntracellularElectrode.")
