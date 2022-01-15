"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import h5py

from ..utils import nwbinspector_check


@nwbinspector_check(severity=1, neurodata_type=pynwb.NWBContainer)
def check_dataset_compression(nwb_container: pynwb.NWBContainer, bytes_threshold=2e6):
    """
    If the data in the TimeSeries object is a h5py.Dataset, check if it has compression enabled.

    Will only run if the size of the h5py.Dataset is larger than bytes_threshold.
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if (
            isinstance(field, h5py.Dataset)
            and field.size * field.dtype.itemsize > bytes_threshold
            and field.compression is None
        ):
            return "Consider enabling compression when writing a large dataset."
