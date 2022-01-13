"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import h5py

from ..utils import add_to_default_checks


@add_to_default_checks(severity=1, neurodata_type=pynwb.NWBContainer)
def check_dataset_compression(nwb_container: pynwb.NWBContainer, bytes_threshold=2e6):
    """
    If the data in the TimeSeries object is a h5py.Dataset, check if it has compression enabled.

    Will only run if the size of the h5py.Dataset is larger than bytes_threshold.
    """
    if (
        not isinstance(nwb_container, pynwb.NWBFile)
        and isinstance(nwb_container.data, h5py.Dataset)
        and nwb_container.data.size * nwb_container.data.dtype.itemsize
        > bytes_threshold
        and nwb_container.data.compression is None
    ):
        return "Consider enabling compression when writing a large dataset."
