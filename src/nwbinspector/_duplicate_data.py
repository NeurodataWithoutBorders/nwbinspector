"""Detection of the same primary data deposited in more than one NWB file.

This check spans multiple files, so it cannot be written as a registered per-object check. Instead, each file is
reduced to a small set of fingerprints, one per primary data array, while ``inspect_all`` reads the folder. The
fingerprints are then grouped by value, which is linear in the number of files and does not require comparing files
pairwise.
"""

import hashlib
from collections import defaultdict
from pathlib import Path
from typing import Iterable, Optional

import numpy as np
from hdmf.common import VectorData
from natsort import natsorted
from pynwb import NWBFile, TimeSeries
from pynwb.misc import Units

from ._registration import Importance, InspectorMessage

CHECK_DUPLICATE_DATA_ACROSS_FILES = "check_duplicate_data_across_files"

# Arrays smaller than this are skipped; short arrays (a handful of trial times, a few event stamps) can match by
# chance and are not what this check is meant to find.
_MIN_NUMBER_OF_ELEMENTS = 100
# Number of evenly spaced blocks read along the first axis of each array.
_NUMBER_OF_BLOCKS = 8
# Approximate number of bytes per block; a block always holds at least one row of the first axis.
_BLOCK_BYTES = 2**16


def _same_file(dataset: object, container_source: Optional[str]) -> bool:
    """Return False when an array is stored in another file (for example, through an HDF5 external link)."""
    dataset_file = getattr(dataset, "file", None)
    dataset_filename = getattr(dataset_file, "filename", None)
    if dataset_filename is None or container_source is None:
        return True
    try:
        return Path(dataset_filename).resolve() == Path(container_source).resolve()
    except (OSError, TypeError, ValueError):
        return True


def _iter_primary_arrays(nwbfile: NWBFile) -> Iterable[tuple[str, object]]:
    """
    Yield ``(location, array)`` for the primary data arrays of an NWBFile.

    Primary data means the data and timestamps of every TimeSeries outside of /stimulus, and the spike times of every
    Units table. Metadata tables such as electrodes, trials and other intervals are not included, because sibling files
    from the same session (raw and processed, one file per probe, and so on) legitimately repeat them.
    """
    stimulus_object_ids = {
        neurodata_object.object_id
        for neurodata_object in list(nwbfile.stimulus.values()) + list(nwbfile.stimulus_template.values())
    }
    container_source = nwbfile.container_source

    for neurodata_object in nwbfile.objects.values():
        if isinstance(neurodata_object, TimeSeries):
            if neurodata_object.object_id in stimulus_object_ids:
                continue
            arrays = [("data", neurodata_object.data), ("timestamps", neurodata_object.timestamps)]
        elif isinstance(neurodata_object, Units):
            spike_times = neurodata_object.get("spike_times") if "spike_times" in neurodata_object.colnames else None
            if spike_times is None:
                continue
            spike_times = getattr(spike_times, "target", spike_times)  # flat VectorData behind the VectorIndex
            if not isinstance(spike_times, VectorData):
                continue
            arrays = [("spike_times", spike_times.data)]
        else:
            continue

        for field_name, array in arrays:
            if array is None or isinstance(array, TimeSeries) or not hasattr(array, "shape"):
                continue  # missing, linked to another TimeSeries, or held in memory as a list
            if not _same_file(dataset=array, container_source=container_source):
                continue
            location = getattr(array, "name", None) or f"{neurodata_object.name}/{field_name}"
            yield location, array


def _is_constant(block: np.ndarray) -> bool:
    values = block.ravel()
    if values.size == 0:
        return True
    if values.dtype.kind in "fc":
        both_nan = np.isnan(values) & np.isnan(values[0])
        return bool(np.all((values == values[0]) | both_nan))
    return bool(np.all(values == values[0]))


def _sample_selection(shape: tuple[int, ...], itemsize: int, fraction: float) -> tuple[slice, ...]:
    """
    Select a block of at most about ``_BLOCK_BYTES`` bytes, positioned at ``fraction`` of the way through the array.

    The block is a run of consecutive rows along the first axis when a row is small. When a single row is itself
    larger than the block size (for example, data written as channels by time), one row is picked and the same rule is
    applied to the next axis, so that memory use stays bounded whatever the shape.
    """
    selection = []
    for axis, length in enumerate(shape):
        bytes_per_item_on_axis = int(np.prod(shape[axis + 1 :], dtype=np.int64)) * itemsize
        if bytes_per_item_on_axis * length <= _BLOCK_BYTES:
            break  # the rest of the array fits in one block
        if bytes_per_item_on_axis <= _BLOCK_BYTES:
            number_of_items = max(1, _BLOCK_BYTES // max(bytes_per_item_on_axis, 1))
            block_start = int(round(fraction * (length - number_of_items)))
            selection.append(slice(block_start, block_start + number_of_items))
            break
        index = int(round(fraction * (length - 1)))
        selection.append(slice(index, index + 1))
    return tuple(selection) if selection else (slice(None),)


def _fingerprint_array(array: object) -> Optional[str]:
    """
    Hash the shape, dtype and a strided sample of an array.

    The sample is a set of evenly spaced blocks through the array, so that two arrays which only share a leading
    segment (a constant baseline, for instance) do not match. Arrays that are too small or that are constant across
    every sampled block return None and are not compared.
    """
    shape = tuple(int(length) for length in array.shape)
    if len(shape) == 0 or int(np.prod(shape, dtype=np.int64)) < _MIN_NUMBER_OF_ELEMENTS:
        return None

    dtype = np.dtype(array.dtype)
    itemsize = max(dtype.itemsize, 1)
    selections = []
    for fraction in np.linspace(0.0, 1.0, _NUMBER_OF_BLOCKS):
        selection = _sample_selection(shape=shape, itemsize=itemsize, fraction=float(fraction))
        if selection not in selections:
            selections.append(selection)

    hasher = hashlib.sha256(repr((shape, dtype.str)).encode())
    first_values = set()
    constant = True
    for selection in selections:
        block = np.asarray(array[selection])
        if block.dtype.kind in "OSU":
            hasher.update(repr(block.tolist()).encode())
        else:
            hasher.update(np.ascontiguousarray(block).tobytes())
        if constant:
            constant = _is_constant(block)
            if constant and block.size > 0:
                first_values.add(repr(block.ravel()[0]))
                constant = len(first_values) == 1

    if constant:
        return None
    return hasher.hexdigest()


def get_primary_data_fingerprints(nwbfile: NWBFile) -> dict[str, list[str]]:
    """
    Fingerprint the primary data arrays of an NWBFile.

    Returns
    -------
    dict
        Maps each fingerprint to the locations of the arrays in this file that produced it.
    """
    fingerprints = defaultdict(list)
    for location, array in _iter_primary_arrays(nwbfile=nwbfile):
        try:
            fingerprint = _fingerprint_array(array=array)
        except Exception:  # an unreadable array is reported by the per-file checks, not here
            continue
        if fingerprint is not None:
            fingerprints[fingerprint].append(location)
    return dict(fingerprints)


def _format_locations(locations: list[str], limit: int = 5) -> str:
    shown = ", ".join(locations[:limit])
    if len(locations) > limit:
        shown += f", and {len(locations) - limit} more"
    return shown


def check_duplicate_data_across_files(
    fingerprints_by_file: dict[str, dict[str, list[str]]],
) -> Iterable[InspectorMessage]:
    """
    Report NWB files that hold the same primary data as another file in the same folder.

    Files whose primary data arrays all match are reported as CRITICAL, since this almost always means a recording
    was deposited twice (sometimes under a different subject or session). Files that share only some of their
    primary arrays are reported as a BEST_PRACTICE_SUGGESTION naming the shared arrays, since a split of one session
    across files can legitimately repeat, for example, a behavioral series.

    Parameters
    ----------
    fingerprints_by_file : dict
        Maps each file path to the output of ``get_primary_data_fingerprints`` for that file.
    """
    files_by_fingerprint = defaultdict(set)
    for file_path, fingerprints in fingerprints_by_file.items():
        for fingerprint in fingerprints:
            files_by_fingerprint[fingerprint].add(file_path)

    # Files with identical, non-empty sets of fingerprints hold the same primary data.
    files_by_full_signature = defaultdict(list)
    for file_path, fingerprints in fingerprints_by_file.items():
        if fingerprints:
            files_by_full_signature[frozenset(fingerprints)].append(file_path)

    reported = set()  # (fingerprint, file set) pairs already covered by a full-match message
    for signature, file_paths in files_by_full_signature.items():
        if len(file_paths) < 2:
            continue
        file_names = natsorted([Path(file_path).name for file_path in file_paths])
        example_file = natsorted(file_paths)[-1]
        locations = natsorted(
            {location for location_list in fingerprints_by_file[example_file].values() for location in location_list}
        )
        for fingerprint in signature:
            reported.add((fingerprint, frozenset(file_paths)))
        yield InspectorMessage(
            message=(
                f"The .nwb files {file_names} contain identical primary data in all {len(signature)} of their "
                f"data arrays ({_format_locations(locations)}). This usually means the same recording was "
                "deposited more than once, possibly under a different subject or session."
            ),
            importance=Importance.CRITICAL,
            check_function_name=CHECK_DUPLICATE_DATA_ACROSS_FILES,
            object_type="NWBFile",
            object_name="root",
            location="/",
            file_path=str(example_file),
        )

    # Remaining shared arrays, grouped by the exact set of files that share them.
    shared_fingerprints_by_file_set = defaultdict(list)
    for fingerprint, file_paths in files_by_fingerprint.items():
        if len(file_paths) < 2:
            continue
        file_set = frozenset(file_paths)
        if (fingerprint, file_set) in reported:
            continue
        shared_fingerprints_by_file_set[file_set].append(fingerprint)

    for file_set, fingerprints in shared_fingerprints_by_file_set.items():
        file_names = natsorted([Path(file_path).name for file_path in file_set])
        example_file = natsorted(file_set)[-1]
        locations = natsorted(
            {location for fingerprint in fingerprints for location in fingerprints_by_file[example_file][fingerprint]}
        )
        yield InspectorMessage(
            message=(
                f"The .nwb files {file_names} share {len(fingerprints)} identical primary data "
                f"array{'s' if len(fingerprints) > 1 else ''} ({_format_locations(locations)}). If these files are "
                "meant to hold different recordings, one of them may contain a copy of the other's data."
            ),
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name=CHECK_DUPLICATE_DATA_ACROSS_FILES,
            object_type="NWBFile",
            object_name="root",
            location="/",
            file_path=str(example_file),
        )
