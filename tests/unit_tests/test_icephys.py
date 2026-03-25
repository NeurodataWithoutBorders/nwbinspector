from datetime import datetime
from uuid import uuid4

import pynwb
from packaging import version
from pynwb import NWBFile
from pynwb.device import Device
from pynwb.file import Subject
from pynwb.icephys import IntracellularElectrode, SweepTable

from nwbinspector import Importance, InspectorMessage
from nwbinspector._nwb_inspection import run_checks
from nwbinspector.checks import (
    check_intracellular_electrode_cell_id_exists,
    check_intracellular_electrode_location_allen_ccf,
    check_sweeptable_deprecated,
)


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


# Create a minimal test SweepTable class that bypasses the deprecation error
# This simulates a SweepTable that would be loaded from an older file
class _TestSweepTable(SweepTable):
    """Test SweepTable for unit tests that bypasses the deprecation check."""

    def __init__(self, name="sweep_table", description="Test sweep table", **kwargs):
        # Set construct mode to bypass deprecation error
        self._in_construct_mode = True
        # Call DynamicTable's __init__ instead of SweepTable's
        super(SweepTable, self).__init__(name=name, description=description, **kwargs)


def test_check_sweeptable_deprecated_with_version_constraint():
    """Test that check_sweeptable_deprecated only runs for NWB schema version > 2.3.0."""
    # Create a minimal NWBFile
    nwbfile = pynwb.NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=datetime.now().astimezone(),
    )

    # Create a test SweepTable object (simulating loading from an older file)
    test_sweep_table = _TestSweepTable(name="sweep_table")

    # Add the SweepTable to the nwbfile's objects manually
    # This simulates having a SweepTable that was loaded from an older file
    nwbfile.objects[test_sweep_table.object_id] = test_sweep_table

    # For NWB version >= 2.4.0, the check should run and return a message
    results = list(
        run_checks(
            nwbfile=nwbfile,
            checks=[check_sweeptable_deprecated],
            nwb_schema_version=version.parse("2.4.0"),
        )
    )
    assert len(results) == 1
    assert "SweepTable is deprecated" in results[0].message
    assert "IntracellularRecordingsTable" in results[0].message

    # For NWB version 2.5.0, the check should also run
    results = list(
        run_checks(
            nwbfile=nwbfile,
            checks=[check_sweeptable_deprecated],
            nwb_schema_version=version.parse("2.5.0"),
        )
    )
    assert len(results) == 1

    # For NWB version <= 2.3.0, the check should be skipped
    results = list(
        run_checks(
            nwbfile=nwbfile,
            checks=[check_sweeptable_deprecated],
            nwb_schema_version=version.parse("2.3.0"),
        )
    )
    assert len(results) == 0

    # For NWB version 2.0.0, the check should also be skipped
    results = list(
        run_checks(
            nwbfile=nwbfile,
            checks=[check_sweeptable_deprecated],
            nwb_schema_version=version.parse("2.0.0"),
        )
    )
    assert len(results) == 0


def test_check_sweeptable_deprecated_message_content():
    """Test the specific message content returned by the check."""
    # Create a minimal NWBFile
    nwbfile = pynwb.NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=datetime.now().astimezone(),
    )

    # Create a test SweepTable object
    test_sweep_table = _TestSweepTable(name="sweep_table")

    # Add to nwbfile objects
    nwbfile.objects[test_sweep_table.object_id] = test_sweep_table

    # Run check with version 2.4.0
    results = list(
        run_checks(
            nwbfile=nwbfile,
            checks=[check_sweeptable_deprecated],
            nwb_schema_version=version.parse("2.4.0"),
        )
    )

    assert len(results) == 1
    assert results[0] == InspectorMessage(
        message=(
            "SweepTable is deprecated in NWB schema version >= 2.4.0. "
            "Use IntracellularRecordingsTable instead. "
            "See NWBFile.add_intracellular_recordings for more information."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_sweeptable_deprecated",
        object_type="_TestSweepTable",
        object_name="sweep_table",
        location="/",
    )


def _make_nwbfile_with_icephys_electrode(location, species=None):
    """Helper to create an NWBFile with an IntracellularElectrode at the given location."""
    nwbfile = NWBFile(
        session_description="test",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    if species is not None:
        nwbfile.subject = Subject(subject_id="001", species=species)
    device = nwbfile.create_device(name="device")
    electrode = nwbfile.create_icephys_electrode(
        name="ielec",
        device=device,
        description="an intracellular electrode",
        location=location,
    )
    return electrode


def test_pass_check_intracellular_electrode_location_allen_ccf():
    electrode = _make_nwbfile_with_icephys_electrode(location="VISp", species="Mus musculus")
    assert check_intracellular_electrode_location_allen_ccf(electrode) is None


def test_pass_check_intracellular_electrode_location_allen_ccf_full_name():
    electrode = _make_nwbfile_with_icephys_electrode(location="Primary visual area", species="Mus musculus")
    assert check_intracellular_electrode_location_allen_ccf(electrode) is None


def test_fail_check_intracellular_electrode_location_allen_ccf():
    electrode = _make_nwbfile_with_icephys_electrode(location="my_custom_region", species="Mus musculus")
    result = check_intracellular_electrode_location_allen_ccf(electrode)
    assert result == InspectorMessage(
        message=(
            "IntracellularElectrode location 'my_custom_region' is not a term in the Allen Mouse Brain CCF ontology. "
            "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
            "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
            "terms do not meet your needs."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_intracellular_electrode_location_allen_ccf",
        object_type="IntracellularElectrode",
        object_name="ielec",
    )


def test_skip_check_intracellular_electrode_location_allen_ccf_non_mouse():
    electrode = _make_nwbfile_with_icephys_electrode(location="my_custom_region", species="Homo sapiens")
    assert check_intracellular_electrode_location_allen_ccf(electrode) is None


def test_skip_check_intracellular_electrode_location_allen_ccf_no_subject():
    electrode = _make_nwbfile_with_icephys_electrode(location="my_custom_region", species=None)
    assert check_intracellular_electrode_location_allen_ccf(electrode) is None
