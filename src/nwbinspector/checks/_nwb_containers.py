"""Check functions that can apply to any object inside an NWBContainer."""

import os
from typing import Iterable, Optional

import h5py
from pynwb import NWBContainer

from .._registration import Importance, InspectorMessage, Severity, register_check
from ..utils import is_module_installed

_HAS_HDMF_ZARR = is_module_installed("hdmf_zarr")
if _HAS_HDMF_ZARR:
    import zarr

    _DATASET_TYPES: tuple = (h5py.Dataset, zarr.Array)
else:
    _DATASET_TYPES = (h5py.Dataset,)


def _get_zarr_compression_indicator(array) -> Optional[object]:
    """Return the compressor(s) of a Zarr array, or None when it is uncompressed.

    zarr-python 3 replaced ``Array.compressor`` with ``Array.compressors``, a tuple that is empty for an uncompressed
    array, and ``compressor`` raises for arrays in the Zarr v3 format. zarr-python 2 only has ``compressor``.
    """
    if hasattr(type(array), "compressors"):
        return array.compressors or None
    return array.compressor


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=NWBContainer)
def check_large_dataset_compression(
    nwb_container: NWBContainer, gb_lower_bound: float = 20.0
) -> Optional[InspectorMessage]:
    """
    If the data in the Container object is a 'large' h5py.Dataset, check if it has compression enabled.

    Will only return an inspector warning if the size of the h5py.Dataset is larger than the
    gb_lower_bound (default of 20 GB).

    Best Practice: :ref:`best_practice_compression`
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if not isinstance(field, _DATASET_TYPES):
            continue

        compression_indicator = None
        if isinstance(field, h5py.Dataset):
            compression_indicator = field.compression
        elif _HAS_HDMF_ZARR and isinstance(field, zarr.Array):
            compression_indicator = _get_zarr_compression_indicator(field)

        field_size_bytes = field.size * field.dtype.itemsize
        if compression_indicator is None and field_size_bytes > gb_lower_bound * 1e9:
            return InspectorMessage(
                severity=Severity.HIGH,
                message=f"{os.path.split(field.name)[1]} is a large uncompressed dataset! Please enable compression.",
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBContainer)
def check_small_dataset_compression(
    nwb_container: NWBContainer,
    gb_severity_threshold: float = 10.0,
    mb_lower_bound: float = 50.0,
    gb_upper_bound: float = 20.0,  # 20 GB upper bound to prevent double-raise
) -> Optional[InspectorMessage]:
    """
    If the data in the Container object is a h5py.Dataset, check if it has compression enabled.

    Will only return an inspector warning if the size of the h5py.Dataset is larger than mb_lower_bound (default 50 MB)
    and smaller than gb_upper_bound (default of 20 GB).

    Best Practice: :ref:`best_practice_compression`
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if not isinstance(field, _DATASET_TYPES):
            continue

        compression_indicator = None
        if isinstance(field, h5py.Dataset):
            compression_indicator = field.compression
        elif _HAS_HDMF_ZARR and isinstance(field, zarr.Array):
            compression_indicator = _get_zarr_compression_indicator(field)

        if (
            compression_indicator is None
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

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBContainer)
def check_single_chunk_dataset(nwb_container: NWBContainer, mb_lower_bound: float = 50.0) -> Optional[InspectorMessage]:
    """
    Check if an HDF5 dataset is written as a single uncompressed chunk that spans the whole dataset.

    That layout carries the overhead of chunked storage without any of its benefits: a reader still has to load the
    whole dataset to access any part of it, and nothing is compressed. Below ``mb_lower_bound`` (default 50 MB) the
    dataset would be better stored contiguously. At or above it, the dataset should be split into several chunks and
    compressed. The missing compression itself is reported by ``check_small_dataset_compression`` and
    ``check_large_dataset_compression``, so this check only speaks to the layout.

    A small dataset that can still be resized is left alone. HDF5 requires chunked storage for a resizable dataset,
    so the contiguous advice cannot be followed, and such a dataset is often a seed that a pipeline appends to later.

    Best Practice: :ref:`best_practice_chunk_data`
    """
    for field in getattr(nwb_container, "fields", dict()).values():
        if not isinstance(field, h5py.Dataset):
            continue
        if field.chunks is None or field.compression is not None or field.size == 0:
            continue
        if any(chunk < size for chunk, size in zip(field.chunks, field.shape)):
            continue

        if field.size * field.dtype.itemsize < mb_lower_bound * 1e6:
            if any(max_size is None or max_size > size for max_size, size in zip(field.maxshape, field.shape)):
                continue
            advice = "Contiguous storage would be a better fit for a dataset of this size."
        else:
            advice = "Split it into several chunks and enable compression."
        return InspectorMessage(
            message=f"{os.path.split(field.name)[1]} is stored as a single uncompressed chunk. {advice}",
        )

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=NWBContainer)
def check_empty_string_for_optional_attribute(nwb_container: NWBContainer) -> Optional[Iterable[InspectorMessage]]:
    """
    Check if any NWBContainer has optional fields that are written as an empty string.

    These values should just be omitted instead.

    Parameters
    ----------
    nwb_container: NWBContainer

    Best Practice: :ref:`best_practice_placeholders`
    """
    docval_args = type(nwb_container).__init__.__docval__["args"]
    optional_attrs = [
        arg["name"] for arg in docval_args if arg["type"] is str and "default" in arg and arg["default"] is None
    ]
    fields = [attr for attr in optional_attrs if getattr(nwb_container, attr) == ""]
    for field in fields:
        yield InspectorMessage(
            message=f'The attribute "{field}" is optional and you have supplied an empty string. Improve by omitting '
            "this attribute (in MatNWB or PyNWB) or entering as None (in PyNWB)"
        )

    return None
