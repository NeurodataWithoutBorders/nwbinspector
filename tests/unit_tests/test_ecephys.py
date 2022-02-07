from pynwb.misc import Units

from nwbinspector import check_negative_spike_times
from nwbinspector.register_checks import InspectorMessage, Importance, Severity


def test_check_negative_spike_times_all_positive():
    units_table = Units()
    units_table.add_unit(spike_times=[0.0, 0.1])
    units_table.add_unit(spike_times=[1.0])
    assert check_negative_spike_times(units_table=units_table) is None


def test_check_negative_spike_times_empty():
    units_table = Units()
    assert check_negative_spike_times(units_table=units_table) is None


def test_check_negative_spike_times_some_negative():
    units_table = Units()
    units_table.add_unit(spike_times=[0.0, 0.1])
    units_table.add_unit(spike_times=[-1.0])
    assert check_negative_spike_times(units_table=units_table) == InspectorMessage(
        severity=Severity.NO_SEVERITY,
        message=(
            "This Units table contains negative spike times. Time should generally be aligned to the earliest time "
            "reference in the NWBFile."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_negative_spike_times",
        object_type="Units",
        object_name="Units",
        location="/",
    )
