import pytest
from packaging.version import Version
from pynwb.icephys import IntracellularElectrode
from pynwb.device import Device

from nwbinspector import InspectorMessage, Importance, check_intracellular_electrode_cell_id_exists
from nwbinspector.utils import get_package_version

PYNWB_VERSION_LOWER_2_1_0 = get_package_version(name="pynwb") < Version("2.1.0")
PYNWB_VERSION_LOWER_SKIP_REASON = "This test requires PyNWB>=2.1.0"


@pytest.mark.skipif(PYNWB_VERSION_LOWER_2_1_0, reason=PYNWB_VERSION_LOWER_SKIP_REASON)
def test_pass_check_intracellular_electrode_cell_id_exists():
    device = Device(name="device")
    ielec = IntracellularElectrode(name="ielec", cell_id="123", device=device, description="an intracellular electrode")
    assert check_intracellular_electrode_cell_id_exists(ielec) is None


@pytest.mark.skipif(PYNWB_VERSION_LOWER_2_1_0, reason=PYNWB_VERSION_LOWER_SKIP_REASON)
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


@pytest.mark.skipif(not PYNWB_VERSION_LOWER_2_1_0, reason="This test requires PyNWB<2.1.0")
def test_skip_check_for_lower_versions():
    device = Device(name="device")
    ielec = IntracellularElectrode(name="ielec", device=device, description="an intracellular electrode")
    assert check_intracellular_electrode_cell_id_exists(ielec) is None
