"""Check functions specific to extracellular electrophysiology neurodata types."""
import numpy as np
from numbers import Real

from pynwb.misc import Units
from pynwb.ecephys import ElectricalSeries

from hdmf.utils import get_data_shape

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_negative_spike_times(units_table: Units):
    """Check if the Units table contains negative spike times."""
    if "spike_times" not in units_table:
        return None
    min_spike_time = np.array(units_table["spike_times"][:], dtype="object").min()
    if not isinstance(min_spike_time, Real):  # If table has only a single unit, will return scalar
        min_spike_time = min_spike_time[0]  # If table has more than one unit, will return a list with a single element
    if min_spike_time < 0:
        return InspectorMessage(
            message=(
                "This Units table contains negative spike times. Time should generally be aligned to the earliest "
                "time reference in the NWBFile."
            )
        )


@register_check(importance=Importance.CRITICAL, neurodata_type=ElectricalSeries)
def check_electrical_series_dims(electrical_series: ElectricalSeries):
    data = electrical_series.data
    electrodes = electrical_series.electrodes

    data_shape = get_data_shape(data, strict_no_data_load=True)
    if data_shape and len(data_shape) == 2 and data_shape[1] != len(electrodes.data):
        if data_shape[0] == len(electrodes.data):
            return InspectorMessage(
                message="The second dimension of data does not match the length of electrodes, "
                "but instead the first does. Data is oriented incorrectly and should be transposed."
            )
        return InspectorMessage(
            message="The second dimension of data does not match the length of electrodes. Your "
            "data may be transposed."
        )
