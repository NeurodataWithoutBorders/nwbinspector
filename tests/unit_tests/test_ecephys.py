from datetime import datetime
from unittest import TestCase
from uuid import uuid4

import numpy as np
from hdmf.common.table import DynamicTable, DynamicTableRegion
from pynwb import NWBFile
from pynwb.ecephys import ElectricalSeries, SpikeEventSeries
from pynwb.misc import Units

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_ascending_spike_times,
    check_data_orientation,
    check_electrical_series_dims,
    check_electrical_series_reference_electrodes_table,
    check_negative_spike_times,
    check_spike_times_not_in_unobserved_interval,
)


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

    def test_ascending_spike_times_invalid(self):
        self.units_table.add_unit(spike_times=[0.2, 0.1, 0.3])  # Non-ascending
        assert check_ascending_spike_times(units_table=self.units_table) == InspectorMessage(
            message="Unit 0 contains non-ascending spike times. Spike times should be sorted in ascending order.",
            importance=Importance.BEST_PRACTICE_VIOLATION,
            check_function_name="check_ascending_spike_times",
            object_type="Units",
            object_name="Units",
            location="/",
        )

    def test_ascending_spike_times_empty(self):
        assert check_ascending_spike_times(units_table=self.units_table) is None

    def test_ascending_spike_times_nelems(self):
        self.units_table.add_unit(spike_times=[0.0, 0.1, 0.05])
        assert check_ascending_spike_times(units_table=self.units_table, nelems=2) is None
