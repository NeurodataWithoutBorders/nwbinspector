"""Check functions specific to extracellular electrophysiology neurodata types."""

from typing import Optional

import numpy as np
from pynwb.ecephys import ElectricalSeries, SpikeEventSeries
from pynwb.misc import Units

from .._registration import Importance, InspectorMessage, register_check
from ..utils import get_data_shape

NELEMS = 200
# Default duration threshold: 1 year in seconds
DURATION_THRESHOLD = 31557600.0


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_negative_spike_times(units_table: Units) -> Optional[InspectorMessage]:
    """Check if the Units table contains negative spike times."""
    if "spike_times" not in units_table:
        return None
    if np.any(np.asarray(units_table["spike_times"].target.data[:]) < 0):
        return InspectorMessage(
            message=(
                "This Units table contains negative spike times. Time should generally be aligned to the earliest "
                "time reference in the NWBFile."
            )
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=ElectricalSeries)
def check_electrical_series_dims(electrical_series: ElectricalSeries) -> Optional[InspectorMessage]:
    """
    Use the length of the linked electrode region to check the data orientation.

    Best Practice: :ref:`best_practice_data_orientation`
    """
    data = electrical_series.data
    electrodes = electrical_series.electrodes

    data_shape = get_data_shape(data, strict_no_data_load=True)

    # For SpikeEventSeries, only perform the check for 3D data
    if isinstance(electrical_series, SpikeEventSeries):
        if data_shape and len(data_shape) == 3 and data_shape[1] != len(electrodes.data):
            if data_shape[0] == len(electrodes.data):
                return InspectorMessage(
                    message=(
                        "The second dimension of data does not match the length of electrodes, "
                        "but instead the first does. Data is oriented incorrectly and should be transposed."
                    )
                )
            return InspectorMessage(
                message=(
                    "The second dimension of data does not match the length of electrodes. Your data may be transposed."
                )
            )
        # Do not warn for 2D SpikeEventSeries
        return None

    # For other ElectricalSeries, keep the original logic
    if data_shape and len(data_shape) == 2 and data_shape[1] != len(electrodes.data):
        if data_shape[0] == len(electrodes.data):
            return InspectorMessage(
                message=(
                    "The second dimension of data does not match the length of electrodes, "
                    "but instead the first does. Data is oriented incorrectly and should be transposed."
                )
            )
        return InspectorMessage(
            message=(
                "The second dimension of data does not match the length of electrodes. Your data may be transposed."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ElectricalSeries)
def check_electrical_series_reference_electrodes_table(
    electrical_series: ElectricalSeries,
) -> Optional[InspectorMessage]:
    """
    Check that the 'electrodes' of an ElectricalSeries references the ElectrodesTable.

    Best Practice: TODO
    """
    if electrical_series.electrodes.table.name != "electrodes":
        return InspectorMessage(message="electrodes does not  reference an electrodes table.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_spike_times_not_in_unobserved_interval(units_table: Units, nunits: int = 4) -> Optional[InspectorMessage]:
    """Check if a Units table has spike times that occur outside of observed intervals."""
    if not units_table.obs_intervals:
        return None
    for unit_spike_times, unit_obs_intervals in zip(
        units_table["spike_times"][:nunits], units_table["obs_intervals"][:nunits]
    ):
        spike_times_array = np.array(unit_spike_times)
        if not all(
            sum(
                [
                    np.logical_and(start <= spike_times_array, spike_times_array <= stop)
                    for start, stop in unit_obs_intervals
                ]
            )
        ):
            return InspectorMessage(
                message=(
                    "This Units table contains spike times that occur during periods of time not labeled as being "
                    "observed intervals."
                )
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_ascending_spike_times(units_table: Units, nelems: Optional[int] = NELEMS) -> Optional[InspectorMessage]:
    """
    Check that the values in the timestamps array are strictly increasing.

    Best Practice :ref:`best_practice_ascending_spike_times`
    """
    if "spike_times" not in units_table:
        return None

    for unit_id in range(len(units_table)):
        spike_times = units_table["spike_times"][unit_id]
        if nelems is not None:
            spike_times = spike_times[:nelems]
        if not np.all(np.diff(spike_times) >= 0):
            return InspectorMessage(
                message=(
                    f"Unit {unit_id} contains non-ascending spike times. "
                    "Spike times should be sorted in ascending order."
                )
            )
    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_units_table_duration(
    units: Units, duration_threshold: float = DURATION_THRESHOLD
) -> Optional[InspectorMessage]:
    """
    Check if the duration of spike times in a Units table exceeds a threshold.

    This check helps identify potential issues where spike times may have been stored
    in the wrong units (e.g., milliseconds instead of seconds) or have other data
    quality issues that result in an unrealistically long recording duration.

    Best Practice :ref:`best_practice_units_table_duration`

    Parameters
    ----------
    units : Units
        The Units table to check.
    duration_threshold : float, optional
        The duration threshold in seconds. If the duration exceeds this value,
        an InspectorMessage is returned. Default is 1 year (31557600 seconds).

    Returns
    -------
    Optional[InspectorMessage]
        An InspectorMessage if the duration exceeds the threshold, None otherwise.
    """
    # Check for spike_times column (Units table)
    if "spike_times" not in units:
        return None

    idxs = units["spike_times"].data[:]

    # remove repeats in idxs array and 0s to remove units with no spikes
    idxs = np.unique(np.asarray(idxs))
    idxs = idxs[idxs != 0]

    spike_times = units["spike_times"].target
    if len(idxs) > 1:
        start = np.min(np.r_[spike_times[0], spike_times[idxs[:-1]]])
    else:
        start = spike_times[0]

    end = np.max(spike_times[idxs - 1])

    if len(spike_times) == 0:
        return None

    start = float(np.min(spike_times))
    end = float(np.max(spike_times))
    duration = end - start

    # Check if duration exceeds threshold
    if duration > duration_threshold:
        # Convert to years for the message
        duration_years = duration / 31557600.0
        threshold_years = duration_threshold / 31557600.0
        return InspectorMessage(
            message=(
                f"Units table has a duration of {duration:.2f} seconds "
                f"({duration_years:.2f} years), which exceeds the threshold of "
                f"{duration_threshold:.2f} seconds ({threshold_years:.2f} years). "
                "This may indicate that spike_times are in the wrong units or there is a data quality issue."
            )
        )

    return None
