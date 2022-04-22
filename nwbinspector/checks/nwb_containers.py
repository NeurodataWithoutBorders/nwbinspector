"""Check functions that can apply to any object inside an NWBContainer."""
import os

import h5py
from pynwb import NWBContainer


from ..register_checks import register_check, Importance, InspectorMessage, Severity


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBContainer)
def check_large_dataset_compression(nwb_container: NWBContainer, gb_lower_bound: float = 20.0):
    """
    If the data in the Container object is a 'large' h5py.Dataset, check if it has compression enabled.

    Will only return an inspector warning if the size of the h5py.Dataset is larger than 20 GB.
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if not isinstance(field, h5py.Dataset):
            continue
        if field.compression is None and field.size * field.dtype.itemsize > gb_lower_bound * 1e9:
            return InspectorMessage(
                severity=Severity.HIGH,
                message=f"{os.path.split(field.name)[1]} is a large uncompressed dataset! Please enable compression.",
            )


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBContainer)
def check_small_dataset_compression(
    nwb_container: NWBContainer,
    gb_severity_threshold: float = 10.0,
    mb_lower_bound: float = 50.0,
    gb_upper_bound: float = 20.0,  # 20 GB upper bound to prevent double-raise
):
    """
    If the data in the Container object is a h5py.Dataset, check if it has compression enabled.

    Will only return an inspector warning if the size of the h5py.Dataset is larger than bytes_threshold.
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if not isinstance(field, h5py.Dataset):
            continue
        if (
            field.compression is None
            and mb_lower_bound * 1e6 < field.size * field.dtype.itemsize < gb_upper_bound * 1e9
        ):
            if field.size * field.dtype.itemsize > gb_severity_threshold * 1e9:
                severity = Severity.HIGH
            else:
                severity = Severity.LOW
            return InspectorMessage(
                severity=severity,
                message=(
                    f"{os.path.split(field.name)[1]} is not compressed. Consider enabling compression when writing a "
                    "dataset."
                ),
            )
