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
    if (
        "data" in nwb_container.__dict__["_AbstractContainer__field_values"]
        and isinstance(nwb_container.data, h5py.Dataset)
        and nwb_container.data.size * nwb_container.data.dtype.itemsize
        > bytes_threshold
        and nwb_container.data.compression is None
    ):
        return "Consider enabling compression when writing a large dataset."
