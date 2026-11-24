"""Check functions specific to extracellular electrophysiology neurodata types."""

from typing import Iterable, Optional

import numpy as np
from pynwb import NWBFile
from pynwb.ecephys import ElectricalSeries, SpikeEventSeries
from pynwb.misc import Units

from ._common import MOUSE_SPECIES_VALUES
from .._internal_configs._allen_ccf import get_allen_ccf_location_terms
from .._registration import Importance, InspectorMessage, register_check
from ..utils import get_data_shape
from ..utils._ordering import default_max_bytes, scan_ascending

NELEMS = 200
# Default duration threshold: 1 year in seconds
DURATION_THRESHOLD = 31557600.0


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_units_table_has_spikes(units_table: Units) -> Optional[InspectorMessage]:
    """
    Check if the Units table is missing a spike_times column.

    Best Practice: :ref:`best_practice_units_table_has_spikes`
    """
    if "spike_times" not in units_table:
        return InspectorMessage(
            message=(
                "This Units table does not have a spike_times column. "
                "A Units table without spike times is likely an error or misuse of the neurodata type."
            )
        )
    return None


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


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_units_resolution_is_set(units_table: Units) -> Optional[InspectorMessage]:
    """
    Check that the Units table has resolution set to a meaningful positive float.

    Best Practice: :ref:`best_practice_units_resolution`
    """
    if "spike_times" not in units_table:
        return None

    resolution = units_table.resolution
    if resolution is not None and not np.isnan(resolution) and resolution > 0:
        return None

    if resolution is None or (isinstance(resolution, float) and np.isnan(resolution)):
        detail = "Units table has spike_times but resolution is not set."
    else:
        detail = f"Units table has spike_times but resolution is set to an invalid value ({resolution})."

    return InspectorMessage(
        message=(
            f"{detail} "
            "Resolution indicates the smallest possible difference between two spike times "
            "and should be a positive float equal to 1/sampling_rate of the recording system "
            "(e.g., Units(resolution=1/30000) for a 30 kHz system). "
            "This information is needed to assess the precision of spike timing data."
        )
    )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Units)
def check_units_resolution_is_valid(units_table: Units) -> Optional[InspectorMessage]:
    """
    Check that the Units table resolution is not suspiciously large.

    A resolution greater than 0.01 seconds (sampling rate below 100 Hz) likely indicates that
    the sampling rate was entered instead of the resolution (1/sampling_rate).

    Best Practice: :ref:`best_practice_units_resolution`
    """
    if "spike_times" not in units_table:
        return None

    resolution = units_table.resolution
    if resolution is None or np.isnan(resolution) or resolution <= 0:
        return None

    if resolution > 0.01:
        return InspectorMessage(
            message=(
                f"Units table resolution is {resolution}, which is unexpectedly large. "
                "Resolution should be 1/sampling_rate (e.g., 1/30000 for a 30 kHz system), "
                "not the sampling rate itself."
            )
        )

    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_spike_times_not_in_samples(units_table: Units, nelems: Optional[int] = 200) -> Optional[InspectorMessage]:
    """
    Check if spike times appear to be sample indices rather than seconds.

    Spike times stored as sample indices are integer-valued. Real spike times in seconds
    have fractional parts at any common electrophysiology sampling rate. If the ``resolution``
    field on the Units table is set to >= 1.0 second, the check is skipped. This serves as
    an escape hatch for the unlikely case where spike time resolution is truly 1 second or
    lower; users must explicitly set this field to suppress the check.

    Best Practice: :ref:`best_practice_spike_times_not_in_samples`
    """
    if "spike_times" not in units_table:
        return None

    if units_table.resolution is not None and units_table.resolution >= 1.0:
        return None

    spike_times_data = units_table["spike_times"].target.data

    if isinstance(spike_times_data, list):
        spike_times_data = np.array(spike_times_data)

    sample = np.array(spike_times_data[:nelems])

    if len(sample) == 0:
        return None

    all_integer_valued = np.all(sample == np.floor(sample))

    if all_integer_valued:
        return InspectorMessage(
            message=(
                "Spike times appear to be in samples rather than seconds. "
                "All sampled spike times are integer-valued. "
                "Spike times should be in seconds (divide by the sampling rate to convert). "
                "If your spike time resolution is truly 1 second or lower, "
                "set Units(resolution=1.0) to suppress this check."
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


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_spike_times_without_nans(units_table: Units) -> Optional[InspectorMessage]:
    """
    Check if the Units table contains NaN values in spike times.

    Best Practice: :ref:`best_practice_spike_times_without_nans`
    """
    if "spike_times" not in units_table:
        return None

    if np.any(np.isnan(np.asarray(units_table["spike_times"].target.data[:]))):
        return InspectorMessage(
            message="Units table contains NaN spike times. Spike times should be valid timestamps in seconds."
        )
    return None


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_ascending_spike_times(
    units_table: Units, nelems: Optional[int] = None, max_bytes: Optional[int] = None
) -> Optional[InspectorMessage]:
    """
    Check that spike times are strictly ascending for each unit.

    Descending spike times always indicate a data error (trial-concatenated times, spike sorting bug,
    or conversion error). Equal consecutive spike times violate the neural refractory period for
    single-unit data. If the ``resolution`` field on the Units table is set, equal consecutive spike
    times are allowed because they may reflect hardware timing precision limits.

    The whole spike_times array is read in chunks, so a problem anywhere in any unit is found. Arrays
    larger than ``max_bytes`` are checked on a sample of chunks plus the first and last spike of every unit.

    Best Practice :ref:`best_practice_ascending_spike_times`

    Parameters
    ----------
    units_table : Units
    nelems : int, optional
        Only check the first ``nelems`` spikes of each unit. The default, None, checks every spike.
    max_bytes : int, optional
        Read budget for the spike_times array. Defaults to 1 GB for local files and 200 MB for streamed files.
    """
    if "spike_times" not in units_table:
        return None

    resolution_is_set = units_table.resolution is not None

    if nelems is not None:
        return _check_ascending_spike_times_first_elements(
            units_table=units_table, nelems=nelems, resolution_is_set=resolution_is_set
        )

    spike_times_index = units_table["spike_times"]
    spike_times_data = spike_times_index.target.data
    if isinstance(spike_times_data, list):
        spike_times_data = np.asarray(spike_times_data)
    n_spikes = len(spike_times_data)
    index = np.asarray(spike_times_index.data[:]).astype(np.int64)
    n_units = len(index)
    if n_units == 0 or n_spikes == 0:
        return None

    unit_starts = np.concatenate([[0], index[:-1]])
    segment_starts = unit_starts[(unit_starts > 0) & (unit_starts < n_spikes)]
    scan = scan_ascending(
        data=spike_times_data, ignore_nan=False, segment_starts=segment_starts, max_bytes=max_bytes
    )

    # Positions are converted to unit rows with the stored index, as a reader would.
    descending_positions = np.asarray(scan.descending_positions, dtype=np.int64)
    descending_units = np.unique(np.searchsorted(index, descending_positions, side="right"))

    if scan.sampled:
        # Also compare the first and last spike of every unit. In a chunked or LINDI-backed array each of these
        # reads pulls in a whole chunk, so only do this when the chunks it touches fit in what is left of the budget.
        first = np.clip(unit_starts, 0, n_spikes - 1)
        last = np.clip(index - 1, 0, n_spikes - 1)
        has_two_spikes = (index - unit_starts) >= 2
        boundary_positions = np.unique(np.concatenate([first[has_two_spikes], last[has_two_spikes]]))
        if not _boundary_reads_fit_budget(
            data=spike_times_data, positions=boundary_positions, n_checked=scan.n_checked, max_bytes=max_bytes
        ):
            boundary_positions = boundary_positions[:0]
            has_two_spikes = np.zeros_like(has_two_spikes)
        boundary_values = (
            dict(zip(boundary_positions.tolist(), np.asarray(spike_times_data[boundary_positions])))
            if len(boundary_positions)
            else {}
        )
        reversed_units = [
            unit
            for unit in np.flatnonzero(has_two_spikes)
            if boundary_values[int(last[unit])] < boundary_values[int(first[unit])]
        ]
        descending_units = np.union1d(descending_units, reversed_units).astype(np.int64)

    if len(descending_units):
        first_unit = int(descending_units[0])
        if len(descending_units) == 1:
            message = f"Unit {first_unit} contains descending spike times, which is always a data error. "
        else:
            message = (
                f"{len(descending_units)} of {n_units} units contain descending spike times (the first is unit "
                f"{first_unit}), which is always a data error. "
            )
        message += "Spike times should be sorted in strictly ascending order."
        message += _spike_times_index_overflow_hint(
            descending_positions=descending_positions, index=index, unit_starts=unit_starts
        )
        if scan.sampled:
            message += (
                f" This was found in a sample of {scan.n_checked:,} of {n_spikes:,} spike times, "
                "so more units may be affected."
            )
        return InspectorMessage(message=message)

    if not resolution_is_set and scan.n_equal > 0:
        unit = int(np.searchsorted(index, scan.first_equal_position, side="right"))
        return InspectorMessage(
            message=(
                f"Unit {unit} contains equal consecutive spike times. "
                "This violates the neural refractory period for single-unit data. "
                "If your recording resolution does not allow distinguishing these spikes, "
                "set the `resolution` field on the Units table to suppress this check."
            )
        )

    return None



def _boundary_reads_fit_budget(data, positions: np.ndarray, n_checked: int, max_bytes: Optional[int]) -> bool:
    """Estimate whether reading single elements at ``positions`` stays within the remaining read budget."""
    if len(positions) == 0:
        return True
    itemsize = np.dtype(getattr(data, "dtype", np.float64)).itemsize
    budget = max_bytes if max_bytes is not None else default_max_bytes(data)
    remaining = budget - n_checked * itemsize
    chunks = getattr(data, "chunks", None)
    if chunks:
        chunk_length = int(chunks[0])
        n_chunks = len(np.unique(positions // chunk_length))
        return n_chunks * chunk_length * itemsize <= remaining
    # Contiguous data: each point read costs a small request, so allow up to a few thousand of them.
    return len(positions) <= 5_000


def _spike_times_index_overflow_hint(
    descending_positions: np.ndarray, index: np.ndarray, unit_starts: np.ndarray
) -> str:
    """
    Recognize spikes moved to the next unit by a spike_times_index entry that wrapped at 2**16.

    If the end index of unit k was stored modulo 65,536, the tail of unit k's train opens unit k + 1, and
    unit k + 1 steps backwards exactly a multiple of 65,536 spikes after its stored start.
    """
    if len(descending_positions) == 0:
        return ""
    units = np.searchsorted(index, descending_positions, side="right")
    offsets = descending_positions - unit_starts[np.clip(units, 0, len(unit_starts) - 1)]
    is_wrap = (offsets > 0) & (offsets % 65536 == 0)
    if not is_wrap.any():
        return ""
    unit = int(units[is_wrap][0])
    offset = int(offsets[is_wrap][0])
    return (
        f" In unit {unit} the first backward step comes exactly {offset:,} spikes ({offset // 65536} x 65,536) "
        f"after the unit's start, which suggests that the end index of unit {unit - 1} in spike_times_index "
        "overflowed a 16-bit integer when the file was written, so its last spikes were assigned to "
        f"unit {unit}."
    )


def _check_ascending_spike_times_first_elements(
    units_table: Units, nelems: int, resolution_is_set: bool
) -> Optional[InspectorMessage]:
    """Check only the first ``nelems`` spike times of each unit (the behavior before full-length scans)."""
    for unit_id in range(len(units_table)):
        spike_times = units_table["spike_times"][unit_id][:nelems]
        diffs = np.diff(spike_times)

        if np.any(diffs < 0):
            return InspectorMessage(
                message=(
                    f"Unit {unit_id} contains descending spike times, which is always a data error. "
                    "Spike times should be sorted in strictly ascending order."
                )
            )

        if not resolution_is_set and np.any(diffs == 0):
            return InspectorMessage(
                message=(
                    f"Unit {unit_id} contains equal consecutive spike times. "
                    "This violates the neural refractory period for single-unit data. "
                    "If your recording resolution does not allow distinguishing these spikes, "
                    "set the `resolution` field on the Units table to suppress this check."
                )
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ElectricalSeries)
def check_electrical_series_unscaled_data(electrical_series: ElectricalSeries) -> Optional[InspectorMessage]:
    """
    Check if an ElectricalSeries has integer data with default conversion and offset values.

    If the data type is an integer (int16, uint16, etc.) and both conversion and offset
    are set to their default values (1.0 and 0.0 respectively), this is likely a mistake
    because the raw integer values are probably not in Volts.

    However, if channel_conversion is set with non-default values (not all 1.0),
    then the conversion factors are properly specified and no warning is needed.

    Best Practice: :ref:`best_practice_electrical_series_unscaled_data`
    """
    data = electrical_series.data
    if data is None or len(data) == 0:
        return None

    # Get dtype - handle both numpy arrays and HDF5 datasets
    if hasattr(data, "dtype"):
        dtype = data.dtype
    else:
        dtype = np.asarray(data[:1]).dtype

    # Only check integer types
    if not np.issubdtype(dtype, np.integer):
        return None

    # Check if using default conversion and offset
    # These are inherited from TimeSeries
    conversion = getattr(electrical_series, "conversion", 1.0)
    offset = getattr(electrical_series, "offset", 0.0)

    # Default values
    default_conversion = 1.0
    default_offset = 0.0

    # If conversion or offset is not default, data scaling is specified
    if conversion != default_conversion or offset != default_offset:
        return None

    # Check channel_conversion - if it exists and has non-default values, that's fine
    channel_conversion = getattr(electrical_series, "channel_conversion", None)
    if channel_conversion is not None:
        channel_conversion_array = np.asarray(channel_conversion)
        # If any channel conversion is not 1.0, the scaling is properly specified
        if not np.allclose(channel_conversion_array, 1.0):
            return None

    return InspectorMessage(
        message=(
            f"ElectricalSeries '{electrical_series.name}' has data with dtype '{dtype}' and "
            f"conversion={conversion} and offset={offset}. This suggests the data is in raw acquisition units "
            "which is not in Volts. Please set the 'conversion' and/or 'offset' fields to convert "
            "the data to Volts, or use 'channel_conversion' for per-channel conversion factors."
        )
    )


@register_check(importance=Importance.CRITICAL, neurodata_type=Units)
def check_units_table_duration(
    units_table: Units, duration_threshold: float = DURATION_THRESHOLD
) -> Optional[InspectorMessage]:
    """
    Check if the duration of spike times in a Units table exceeds a threshold.

    This check helps identify potential issues where spike times may have been stored
    in the wrong units (e.g., milliseconds instead of seconds) or have other data
    quality issues that result in an unrealistically long recording duration.

    Best Practice :ref:`best_practice_units_table_duration`

    Parameters
    ----------
    units_table : Units
        The Units table to check.
    duration_threshold : float, optional
        The duration threshold in seconds. If the duration exceeds this value,
        an InspectorMessage is returned. Default is 1 year (31557600 seconds).

    Returns
    -------
    Optional[InspectorMessage]
        An InspectorMessage if the duration exceeds the threshold, None otherwise.
    """
    if "spike_times" not in units_table:
        return None

    # Read the index array (cumulative indices marking end of each unit's spikes)
    # This is small - just one integer per unit
    idxs = np.asarray(units_table["spike_times"].data[:])

    if len(idxs) == 0:
        return None

    # Build indices for first and last spike of each unit
    # First spike indices: 0 for first unit, then idxs[:-1] for subsequent units
    # Last spike indices: idxs - 1 for each unit
    # The leading zero must share the dtype of the index array: mixing uint64 with a signed integer array
    # promotes the result to float64, which cannot be used as a fancy index
    first_spike_idxs = np.concatenate([np.zeros(shape=1, dtype=idxs.dtype), idxs[idxs != idxs[-1]]])
    last_spike_idxs = idxs[idxs != 0] - 1

    # Combine into single array of indices to read, then read all at once
    all_indices = np.concatenate([first_spike_idxs, last_spike_idxs])
    all_indices = np.unique(all_indices)  # Remove duplicates for efficiency

    # Read only the needed spike times in one operation
    spike_times_data = units_table["spike_times"].target.data

    # needed to get tests to work on example data that is a list, not an h5py dataset
    if isinstance(spike_times_data, list):
        spike_times_data = np.array(spike_times_data)

    boundary_spike_times = spike_times_data[all_indices]

    if len(boundary_spike_times) == 0:
        return None

    start = float(np.min(boundary_spike_times))
    end = float(np.max(boundary_spike_times))
    duration = end - start

    if duration > duration_threshold:
        duration_years = duration / DURATION_THRESHOLD
        threshold_years = duration_threshold / DURATION_THRESHOLD
        return InspectorMessage(
            message=(
                f"Units table has a duration of {duration:.2f} seconds "
                f"({duration_years:.2f} years), which exceeds the threshold of "
                f"{duration_threshold:.2f} seconds ({threshold_years:.2f} years). "
                "This may indicate that spike_times are not in seconds that or there is a data quality issue."
            )
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBFile)
def check_electrodes_location_allen_ccf(nwbfile: NWBFile) -> Optional[Iterable[InspectorMessage]]:
    """
    Check that electrode locations are terms in the Allen Mouse Brain CCF ontology.

    Only applies when the subject species is mouse.

    Best Practice: :ref:`best_practice_ecephys_ontologies`
    """
    if nwbfile.subject is None:
        return None
    species = nwbfile.subject.species
    if species not in MOUSE_SPECIES_VALUES:
        return None
    if nwbfile.electrodes is None:
        return None
    if "location" not in nwbfile.electrodes.colnames:
        return None

    valid_terms = get_allen_ccf_location_terms()
    invalid_locations = set()
    for location in nwbfile.electrodes["location"].data:
        if location not in valid_terms and location not in invalid_locations:
            invalid_locations.add(location)
            yield InspectorMessage(
                message=(
                    f"Electrode location '{location}' is not a term in the Allen Mouse Brain CCF ontology. "
                    "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
                    "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
                    "terms do not meet your needs."
                )
            )

    return None
