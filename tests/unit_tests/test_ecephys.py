from datetime import datetime
from unittest import TestCase
from uuid import uuid4

import numpy as np
from hdmf.common.table import DynamicTable, DynamicTableRegion
from pynwb import NWBFile
from pynwb.ecephys import ElectricalSeries, SpikeEventSeries
from pynwb.file import Subject
from pynwb.misc import Units

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_ascending_spike_times,
    check_data_orientation,
    check_electrical_series_dims,
    check_electrical_series_reference_electrodes_table,
    check_electrical_series_unscaled_data,
    check_electrodes_location_allen_ccf,
    check_negative_spike_times,
    check_spike_times_not_in_samples,
    check_spike_times_not_in_unobserved_interval,
    check_units_resolution_is_set,
    check_units_resolution_is_valid,
    check_units_table_duration,
    check_units_table_has_spikes,
)


def test_check_units_table_has_spikes_fail():
    units_table = Units()
    units_table.add_unit()
    assert check_units_table_has_spikes(units_table=units_table) == InspectorMessage(
        message=(
            "This Units table does not have a spike_times column. "
            "A Units table without spike times is likely an error or misuse of the neurodata type."
        ),
        importance=Importance.CRITICAL,
        check_function_name="check_units_table_has_spikes",
        object_type="Units",
        object_name="Units",
        location="/",
    )


def test_check_units_table_has_spikes_pass():
    units_table = Units()
    units_table.add_unit(spike_times=[0.0, 0.1])
    assert check_units_table_has_spikes(units_table=units_table) is None


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


def test_check_units_resolution_is_set_fail_not_set():
    """Units with spike_times but no resolution set should fail."""
    units_table = Units()
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_set(units_table) == InspectorMessage(
        message=(
            "Units table has spike_times but resolution is not set. "
            "Resolution indicates the smallest possible difference between two spike times "
            "and should be a positive float equal to 1/sampling_rate of the recording system "
            "(e.g., Units(resolution=1/30000) for a 30 kHz system). "
            "This information is needed to assess the precision of spike timing data."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_units_resolution_is_set",
        object_type="Units",
        object_name="Units",
        location="/",
    )


def test_check_units_resolution_is_set_pass_positive_float():
    """Units with resolution set to a meaningful positive float should pass."""
    units_table = Units(resolution=1 / 30000)
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_set(units_table) is None


def test_check_units_resolution_is_set_fail_nan():
    """Units with resolution set to NaN should fail."""
    units_table = Units(resolution=float("nan"))
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_set(units_table) is not None


def test_check_units_resolution_is_set_fail_zero():
    """Units with resolution set to 0.0 should fail."""
    units_table = Units(resolution=0.0)
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_set(units_table) is not None


def test_check_units_resolution_is_set_fail_negative():
    """Units with resolution set to a negative value should fail."""
    units_table = Units(resolution=-1.0)
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_set(units_table) is not None


def test_check_units_resolution_is_valid_fail_sampling_rate():
    """Resolution set to a sampling rate value (e.g., 30000) should fail."""
    units_table = Units(resolution=30000.0)
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_valid(units_table) == InspectorMessage(
        message=(
            "Units table resolution is 30000.0, which is unexpectedly large. "
            "Resolution should be 1/sampling_rate (e.g., 1/30000 for a 30 kHz system), "
            "not the sampling rate itself."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_units_resolution_is_valid",
        object_type="Units",
        object_name="Units",
        location="/",
    )


def test_check_units_resolution_is_valid_pass_valid():
    """Resolution of 1/30000 should pass."""
    units_table = Units(resolution=1 / 30000)
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_valid(units_table) is None


def test_check_units_resolution_is_valid_skip_not_set():
    """Units with resolution not set should pass."""
    units_table = Units()
    units_table.add_unit(spike_times=[0.1, 0.2, 0.3])
    assert check_units_resolution_is_valid(units_table) is None


def test_check_spike_times_not_in_samples_fail():
    """Integer-valued spike times with large magnitude - likely sample indices."""
    units_table = Units()
    units_table.add_unit(spike_times=[30000.0, 60000.0, 90000.0])
    units_table.add_unit(spike_times=[30001.0, 60002.0, 90003.0])
    assert check_spike_times_not_in_samples(units_table) == InspectorMessage(
        message=(
            "Spike times appear to be in samples rather than seconds. "
            "All sampled spike times are integer-valued. "
            "Spike times should be in seconds (divide by the sampling rate to convert). "
            "If your spike time resolution is truly 1 second or lower, "
            "set Units(resolution=1.0) to suppress this check."
        ),
        importance=Importance.CRITICAL,
        check_function_name="check_spike_times_not_in_samples",
        object_type="Units",
        object_name="Units",
        location="/",
    )


def test_check_spike_times_not_in_samples_pass_real_times():
    """Float spike times in seconds - normal data."""
    units_table = Units()
    units_table.add_unit(spike_times=[0.1234, 1.5678, 3.9012])
    units_table.add_unit(spike_times=[10.111, 20.222, 30.333])
    assert check_spike_times_not_in_samples(units_table) is None


def test_check_spike_times_not_in_samples_pass_resolution_escape_hatch():
    """Resolution set to >= 1.0 skips the check.

    This is an escape hatch for the unlikely case where spike time resolution
    is truly 1 second or lower (e.g. behavioral timestamps). Users must explicitly
    set the resolution field on the Units table to suppress this check.
    """
    units_table = Units(resolution=1.0)
    units_table.add_unit(spike_times=[1.0, 2.0, 3.0, 100.0, 200.0])
    assert check_spike_times_not_in_samples(units_table) is None


class TestCheckElectricalSeries(TestCase):
    def setUp(self):
        nwbfile = NWBFile(
            session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone()
        )

        device = nwbfile.create_device(name="dev")
        group = nwbfile.create_electrode_group(
            name="electrode_group", description="desc", location="loc", device=device
        )

        for _ in range(5):
            nwbfile.add_electrode(
                x=3.0,
                y=3.0,
                z=3.0,
                imp=-1.0,
                location="unknown",
                filtering="unknown",
                group=group,
            )
        self.nwbfile = nwbfile

    def test_check_electrical_series_wrong_dims(self):
        electrodes = self.nwbfile.create_electrode_table_region(region=[1, 2, 3], description="three elecs")

        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 10)),
            electrodes=electrodes,
            rate=30.0,
        )

        self.nwbfile.add_acquisition(electrical_series)

        assert check_electrical_series_dims(self.nwbfile.acquisition["elec_series"]) == InspectorMessage(
            message=(
                "The second dimension of data does not match the length of electrodes. Your data may be transposed."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_electrical_series_dims",
            object_type="ElectricalSeries",
            object_name="elec_series",
        )

    def test_check_electrical_series_flipped(self):
        electrodes = self.nwbfile.create_electrode_table_region(region=[0, 1, 2, 3, 4], description="all")

        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((5, 100)),
            electrodes=electrodes,
            rate=30.0,
        )

        self.nwbfile.add_acquisition(electrical_series)

        assert check_electrical_series_dims(self.nwbfile.acquisition["elec_series"]) == InspectorMessage(
            message=(
                "The second dimension of data does not match the length of electrodes, but instead the first does. "
                "Data is oriented incorrectly and should be transposed."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_electrical_series_dims",
            object_type="ElectricalSeries",
            object_name="elec_series",
        )

    def test_pass(self):
        electrodes = self.nwbfile.create_electrode_table_region(region=[0, 1, 2, 3, 4], description="all")

        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 5)),
            electrodes=electrodes,
            rate=30.0,
        )

        self.nwbfile.add_acquisition(electrical_series)

        assert check_electrical_series_dims(electrical_series) is None
        assert check_electrical_series_reference_electrodes_table(electrical_series) is None

    def test_trigger_check_electrical_series_reference_electrodes_table(self):
        dyn_tab = DynamicTable(name="name", description="desc")
        dyn_tab.add_column("group_name", "desc")
        for i in range(5):
            dyn_tab.add_row(group_name=1)
        dynamic_table_region = DynamicTableRegion(
            name="electrodes", description="I am wrong", data=[0, 1, 2, 3, 4], table=dyn_tab
        )

        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 5)),
            electrodes=dynamic_table_region,
            rate=30.0,
        )

        assert (
            check_electrical_series_reference_electrodes_table(electrical_series).message
            == "electrodes does not  reference an electrodes table."
        )


class TestCheckSpikeEventSeries(TestCase):
    def setUp(self):
        nwbfile = NWBFile(
            session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone()
        )
        device = nwbfile.create_device(name="dev")
        group = nwbfile.create_electrode_group(
            name="electrode_group", description="desc", location="loc", device=device
        )
        for _ in range(3):
            nwbfile.add_electrode(location="unknown", group=group)
        self.nwbfile = nwbfile

    def test_check_data_orientation_spike_event_series(self):
        """Test that SpikeEventSeries with more waveform samples than events doesn't trigger the data orientation check."""

        # create data with shape (events, channels, waveform_samples) where waveform_samples > events
        data = np.zeros((5, 3, 10))
        timestamps = np.arange(5)
        electrodes = self.nwbfile.create_electrode_table_region(region=[0, 1, 2], description="three elecs")

        spike_event_series = SpikeEventSeries(
            name="spike_events",
            description="test spike events",
            data=data,
            timestamps=timestamps,
            electrodes=electrodes,
        )

        assert check_data_orientation(spike_event_series) is None

    def test_spikeeventseries_dims_check(self):
        """
        Test that 2D SpikeEventSeries does not trigger a warning,
        but 3D SpikeEventSeries with mismatched electrodes does.
        """

        electrodes = self.nwbfile.create_electrode_table_region(region=[0, 1, 2], description="three elecs")

        # 2D data: [num_events, num_samples] (should NOT trigger warning)
        ses_2d = SpikeEventSeries(
            name="spike_events_2d",
            data=np.zeros((10, 5)),
            electrodes=electrodes,
            timestamps=[0.1 * i for i in range(10)],
        )
        assert check_electrical_series_dims(ses_2d) is None

        # 3D data: [num_events, num_channels, num_samples] with mismatched num_channels (should trigger warning)
        ses_3d = SpikeEventSeries(
            name="spike_events_3d",
            data=np.zeros((10, 4, 5)),  # 4 != 3 electrodes
            electrodes=electrodes,
            timestamps=[0.1 * i for i in range(10)],
        )
        result = check_electrical_series_dims(ses_3d)
        assert result == InspectorMessage(
            message=(
                "The second dimension of data does not match the length of electrodes. Your data may be transposed."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_electrical_series_dims",
            object_type="SpikeEventSeries",
            object_name="spike_events_3d",
            location="/",
        )


def test_check_spike_times_not_in_unobserved_interval_pass():
    units_table = Units(name="TestUnits")
    units_table.add_unit(spike_times=[1, 2, 3], obs_intervals=[[0, 2.5], [2.7, 3.5]])
    assert check_spike_times_not_in_unobserved_interval(units_table=units_table) is None


def test_check_spike_times_not_in_unobserved_interval_pass_no_intervals():
    units_table = Units(name="TestUnits")
    units_table.add_unit(spike_times=[1, 2, 3])
    assert check_spike_times_not_in_unobserved_interval(units_table=units_table) is None


def test_check_spike_times_not_in_unobserved_interval_1():
    units_table = Units(name="TestUnits")
    units_table.add_unit(spike_times=[1, 2, 3], obs_intervals=[[0, 2.5], [3.5, 4]])
    assert check_spike_times_not_in_unobserved_interval(units_table=units_table) == InspectorMessage(
        message=(
            "This Units table contains spike times that occur during periods of time not labeled as being "
            "observed intervals."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_spike_times_not_in_unobserved_interval",
        object_type="Units",
        object_name="TestUnits",
        location="/",
    )


def test_check_spike_times_not_in_unobserved_interval_2():
    units_table = Units(name="TestUnits")
    units_table.add_unit(spike_times=[1, 2, 3, 4, 5, 6], obs_intervals=[[0, 2.5], [3.5, 7]])
    assert check_spike_times_not_in_unobserved_interval(units_table=units_table) == InspectorMessage(
        message=(
            "This Units table contains spike times that occur during periods of time not labeled as being "
            "observed intervals."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_spike_times_not_in_unobserved_interval",
        object_type="Units",
        object_name="TestUnits",
        location="/",
    )


def test_check_spike_times_not_in_unobserved_interval_multiple_units():
    units_table = Units(name="TestUnits")
    units_table.add_unit(spike_times=[1, 2, 3, 4, 5, 6], obs_intervals=[[0, 3.2], [3.5, 7]])
    units_table.add_unit(spike_times=[6.5, 12, 13, 14, 15, 16], obs_intervals=[[10, 15.2], [15.8, 17]])
    assert check_spike_times_not_in_unobserved_interval(units_table=units_table) == InspectorMessage(
        message=(
            "This Units table contains spike times that occur during periods of time not labeled as being "
            "observed intervals."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_spike_times_not_in_unobserved_interval",
        object_type="Units",
        object_name="TestUnits",
        location="/",
    )


class TestCheckAscendingSpikeTimes(TestCase):
    def setUp(self):
        self.units_table = Units()

    def test_ascending_spike_times_valid(self):
        self.units_table.add_unit(spike_times=[0.0, 0.1, 0.2])
        self.units_table.add_unit(spike_times=[1.0, 1.1, 1.2])
        assert check_ascending_spike_times(units_table=self.units_table) is None

    def test_descending_spike_times(self):
        self.units_table.add_unit(spike_times=[0.2, 0.1, 0.3])
        assert check_ascending_spike_times(units_table=self.units_table) == InspectorMessage(
            message=(
                "Unit 0 contains descending spike times, which is always a data error. "
                "Spike times should be sorted in strictly ascending order."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_ascending_spike_times",
            object_type="Units",
            object_name="Units",
            location="/",
        )

    def test_equal_consecutive_spike_times_no_resolution(self):
        self.units_table.add_unit(spike_times=[0.0, 0.1, 0.1, 0.2])
        assert check_ascending_spike_times(units_table=self.units_table) == InspectorMessage(
            message=(
                "Unit 0 contains equal consecutive spike times. "
                "This violates the neural refractory period for single-unit data. "
                "If your recording resolution does not allow distinguishing these spikes, "
                "set the `resolution` field on the Units table to suppress this check."
            ),
            importance=Importance.CRITICAL,
            check_function_name="check_ascending_spike_times",
            object_type="Units",
            object_name="Units",
            location="/",
        )

    def test_equal_consecutive_spike_times_with_resolution(self):
        units_table = Units(resolution=0.001)
        units_table.add_unit(spike_times=[0.0, 0.1, 0.1, 0.2])
        assert check_ascending_spike_times(units_table=units_table) is None

    def test_ascending_spike_times_empty(self):
        assert check_ascending_spike_times(units_table=self.units_table) is None

    def test_ascending_spike_times_nelems(self):
        self.units_table.add_unit(spike_times=[0.0, 0.1, 0.05])
        assert check_ascending_spike_times(units_table=self.units_table, nelems=2) is None


def test_check_units_table_duration_pass():
    """Test that units table with reasonable duration passes."""
    units = Units(name="units")
    units.add_unit(spike_times=[0.0, 1.0, 2.0])
    units.add_unit(spike_times=[0.5, 1.5, 3.0])

    assert check_units_table_duration(units) is None


def test_check_units_table_duration_pass_empty_spike_times():
    """Test that units table with no spike times passes."""
    units = Units(name="units")
    # Add a unit without spike_times
    units.add_column(name="custom_col", description="test")
    units.add_row(custom_col=1)

    assert check_units_table_duration(units) is None


def test_check_units_table_duration_fail():
    """Test that units table with excessive duration fails."""
    units = Units(name="units")
    # Add spike times spanning more than 1 year (> 31557600 seconds)
    units.add_unit(spike_times=[0.0, 1.0, 2.0])
    units.add_unit(spike_times=[0.5, 1.5, 40000000.0])  # ~1.27 years

    result = check_units_table_duration(units)
    assert result == InspectorMessage(
        message=(
            "Units table has a duration of 40000000.00 seconds "
            "(1.27 years), which exceeds the threshold of "
            "31557600.00 seconds (1.00 years). "
            "This may indicate that spike_times are not in seconds that or there is a data quality issue."
        ),
        importance=Importance.CRITICAL,
        check_function_name="check_units_table_duration",
        object_type="Units",
        object_name="units",
        location="/",
    )


def test_check_units_table_duration_custom_threshold():
    """Test units table duration check with custom threshold."""
    units = Units(name="units")
    units.add_unit(spike_times=[0.0, 100.0])  # 100 seconds

    # Should pass with default threshold
    assert check_units_table_duration(units) is None

    # Should fail with custom threshold of 50 seconds
    result = check_units_table_duration(units, duration_threshold=50.0)
    assert result == InspectorMessage(
        message=(
            "Units table has a duration of 100.00 seconds "
            "(0.00 years), which exceeds the threshold of "
            "50.00 seconds (0.00 years). "
            "This may indicate that spike_times are not in seconds that or there is a data quality issue."
        ),
        importance=Importance.CRITICAL,
        check_function_name="check_units_table_duration",
        object_type="Units",
        object_name="units",
        location="/",
    )


def test_check_units_table_duration_single_unit():
    """Test that units table with a single unit and long duration is detected."""
    units = Units(name="units")
    units.add_unit(spike_times=[0.0, 50000000.0])  # ~1.58 years

    result = check_units_table_duration(units)
    assert result is not None
    assert "Units table has a duration of 50000000.00 seconds" in result.message


def test_check_units_table_duration_first_unit_no_spikes():
    """Test handling of empty spike_times for the first unit.

    The first unit is a special case in the index structure: it has no preceding
    index value, so when the first unit has no spikes, the index array starts as
    [0, ...] (the first value equals the second). This test ensures the duration
    calculation correctly handles this edge case without index errors.
    """
    units = Units(name="units")
    units.add_unit(spike_times=[])  # First unit has no spikes
    units.add_unit(spike_times=[0.0, 1.0, 2.0])  # Second unit has spikes

    # Should pass - duration is only 2 seconds
    assert check_units_table_duration(units) is None


def test_check_units_table_duration_second_unit_no_spikes():
    """Test handling of empty spike_times for a non-first unit.

    Non-first units with no spikes produce a different index pattern than the
    first unit: the index array contains [..., x, x, ...] where consecutive
    values are equal. This test ensures the duration calculation correctly
    handles this distinct edge case.
    """
    units = Units(name="units")
    units.add_unit(spike_times=[0.0, 1.0, 2.0])  # First unit has spikes
    units.add_unit(spike_times=[])  # Second unit has no spikes

    # Should pass - duration is only 2 seconds
    assert check_units_table_duration(units) is None


class TestCheckElectricalSeriesUnscaledData(TestCase):
    """Tests for check_electrical_series_unscaled_data."""

    def setUp(self):
        nwbfile = NWBFile(
            session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone()
        )
        device = nwbfile.create_device(name="dev")
        group = nwbfile.create_electrode_group(
            name="electrode_group", description="desc", location="loc", device=device
        )
        for _ in range(3):
            nwbfile.add_electrode(location="unknown", group=group)
        self.nwbfile = nwbfile
        self.electrodes = self.nwbfile.create_electrode_table_region(region=[0, 1, 2], description="three elecs")

    def test_pass_with_float_data(self):
        """Test that float data does not trigger a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.float64),
            electrodes=self.electrodes,
            rate=30.0,
        )
        assert check_electrical_series_unscaled_data(electrical_series) is None

    def test_pass_with_int_data_and_non_default_conversion(self):
        """Test that int data with non-default conversion does not trigger a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.int16),
            electrodes=self.electrodes,
            rate=30.0,
            conversion=1e-6,  # Non-default conversion
        )
        assert check_electrical_series_unscaled_data(electrical_series) is None

    def test_pass_with_int_data_and_non_default_offset(self):
        """Test that int data with non-default offset does not trigger a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.int16),
            electrodes=self.electrodes,
            rate=30.0,
            offset=0.5,  # Non-default offset
        )
        assert check_electrical_series_unscaled_data(electrical_series) is None

    def test_pass_with_int_data_and_channel_conversion(self):
        """Test that int data with channel_conversion set does not trigger a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.int16),
            electrodes=self.electrodes,
            rate=30.0,
            channel_conversion=[1e-6, 1e-6, 1e-6],  # Non-default channel conversion
        )
        assert check_electrical_series_unscaled_data(electrical_series) is None

    def test_fail_with_int16_data_and_default_conversion(self):
        """Test that int16 data with default conversion triggers a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.int16),
            electrodes=self.electrodes,
            rate=30.0,
        )
        result = check_electrical_series_unscaled_data(electrical_series)
        assert result is not None
        assert result == InspectorMessage(
            message=(
                "ElectricalSeries 'elec_series' has data with dtype 'int16' and "
                "conversion=1.0 and offset=0.0. This suggests the data is in raw acquisition units "
                "which is not in Volts. Please set the 'conversion' and/or 'offset' fields to convert "
                "the data to Volts, or use 'channel_conversion' for per-channel conversion factors."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_electrical_series_unscaled_data",
            object_type="ElectricalSeries",
            object_name="elec_series",
            location="/",
        )

    def test_fail_with_uint16_data_and_default_conversion(self):
        """Test that uint16 data with default conversion triggers a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.uint16),
            electrodes=self.electrodes,
            rate=30.0,
        )
        result = check_electrical_series_unscaled_data(electrical_series)
        assert result == InspectorMessage(
            message=(
                "ElectricalSeries 'elec_series' has data with dtype 'uint16' and "
                "conversion=1.0 and offset=0.0. This suggests the data is in raw acquisition units "
                "which is not in Volts. Please set the 'conversion' and/or 'offset' fields to convert "
                "the data to Volts, or use 'channel_conversion' for per-channel conversion factors."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_electrical_series_unscaled_data",
            object_type="ElectricalSeries",
            object_name="elec_series",
            location="/",
        )

    def test_fail_with_channel_conversion_all_ones(self):
        """Test that int data with channel_conversion all 1.0 triggers a warning."""
        electrical_series = ElectricalSeries(
            name="elec_series",
            description="desc",
            data=np.zeros((100, 3), dtype=np.int16),
            electrodes=self.electrodes,
            rate=30.0,
            channel_conversion=[1.0, 1.0, 1.0],  # All default values
        )
        result = check_electrical_series_unscaled_data(electrical_series)
        assert result == InspectorMessage(
            message=(
                "ElectricalSeries 'elec_series' has data with dtype 'int16' and "
                "conversion=1.0 and offset=0.0. This suggests the data is in raw acquisition units "
                "which is not in Volts. Please set the 'conversion' and/or 'offset' fields to convert "
                "the data to Volts, or use 'channel_conversion' for per-channel conversion factors."
            ),
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_electrical_series_unscaled_data",
            object_type="ElectricalSeries",
            object_name="elec_series",
            location="/",
        )


def _make_nwbfile_with_electrodes(locations, species=None):
    """Helper to create an NWBFile with electrodes at the given locations."""
    nwbfile = NWBFile(
        session_description="test",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    if species is not None:
        nwbfile.subject = Subject(subject_id="001", species=species)
    device = nwbfile.create_device(name="dev")
    group = nwbfile.create_electrode_group(name="electrode_group", description="desc", location="brain", device=device)
    for loc in locations:
        nwbfile.add_electrode(location=loc, group=group)
    return nwbfile


def test_pass_check_electrodes_location_allen_ccf():
    nwbfile = _make_nwbfile_with_electrodes(
        locations=["VISp", "CA1", "Primary motor area"],
        species="Mus musculus",
    )
    assert check_electrodes_location_allen_ccf(nwbfile) is None


def test_fail_check_electrodes_location_allen_ccf():
    nwbfile = _make_nwbfile_with_electrodes(
        locations=["VISp", "my_region", "CA1", "another_region", "my_region"],
        species="Mus musculus",
    )
    results = list(check_electrodes_location_allen_ccf(nwbfile))
    assert len(results) == 2
    assert results[0] == InspectorMessage(
        message=(
            "Electrode location 'my_region' is not a term in the Allen Mouse Brain CCF ontology. "
            "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
            "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
            "terms do not meet your needs."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_electrodes_location_allen_ccf",
        object_type="NWBFile",
        object_name="root",
        location="/",
    )
    assert "another_region" in results[1].message


def test_skip_check_electrodes_location_allen_ccf_non_mouse():
    nwbfile = _make_nwbfile_with_electrodes(
        locations=["my_region"],
        species="Homo sapiens",
    )
    assert check_electrodes_location_allen_ccf(nwbfile) is None


def test_skip_check_electrodes_location_allen_ccf_no_electrodes():
    nwbfile = NWBFile(
        session_description="test",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    nwbfile.subject = Subject(subject_id="001", species="Mus musculus")
    assert check_electrodes_location_allen_ccf(nwbfile) is None


def test_skip_check_electrodes_location_allen_ccf_no_subject():
    nwbfile = _make_nwbfile_with_electrodes(
        locations=["my_region"],
        species=None,
    )
    assert check_electrodes_location_allen_ccf(nwbfile) is None
