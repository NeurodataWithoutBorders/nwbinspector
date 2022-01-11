"""Authors: Cody Baker and Ben Dichter."""
import h5py

from .utils import add_to_default_checks


@add_to_default_checks(severity=1)
def check_dataset_compression(obj, bytes_threshold=2e6):
    """If the Dataset object is larger than bytes_threshold, check if it has compression enabled."""
    if isinstance(obj, h5py.Dataset):
        if obj.size * obj.dtype.itemsize > bytes_threshold and obj.compression is None:
            return "Consider enabling compression when writing a large dataset."
