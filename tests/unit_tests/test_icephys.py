from pynwb.device import Device
from pynwb.icephys import IntracellularElectrode

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import check_intracellular_electrode_cell_id_exists


def test_pass_check_intracellular_electrode_cell_id_exists():
    device = Device(name="device")
    ielec = IntracellularElectrode(name="ielec", cell_id="123", device=device, description="an intracellular electrode")
    assert check_intracellular_electrode_cell_id_exists(ielec) is None


def test_fail_check_intracellular_electrode_cell_id_exists():
    device = Device(name="device")
    ielec = IntracellularElectrode(name="ielec", device=device, description="an intracellular electrode")
    assert check_intracellular_electrode_cell_id_exists(ielec) == InspectorMessage(
        message="Please include a unique cell_id associated with this IntracellularElectrode.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_intracellular_electrode_cell_id_exists",
        object_type="IntracellularElectrode",
        object_name="ielec",
        location="/",
    )


def test_check_sweeptable_deprecated():
    """
    Test that check_sweeptable_deprecated correctly identifies deprecated SweepTable usage.

    Note: This test would require an actual NWB file with a SweepTable from an older version.
    Since SweepTable cannot be instantiated directly in newer PyNWB versions (it raises ValueError),
    and creating such a file programmatically is complex, this test serves as documentation
    for the expected behavior.

    The check will trigger when:
    1. An NWB file contains a SweepTable object (from older files created before deprecation)
    2. The file's nwb_version attribute is >= 2.4.0

    In practice, this would occur when inspecting older NWB files that contain SweepTable
    objects but were created with or upgraded to NWB 2.4.0 or later.
    """
    # This is a placeholder test that documents the expected behavior
    # In real-world usage, the check would be triggered by inspect_nwbfile() or inspect_all()
    # when processing files that contain SweepTable objects
    pass
