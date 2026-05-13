"""Helpers for reading an NWB file with backend detection and streaming support."""

from pathlib import Path
from typing import Literal, Optional, Union
from warnings import filterwarnings, warn

import h5py
from hdmf.backends.io import HDMFIO
from pynwb import NWBHDF5IO, NWBFile, read_nwb

from ..utils import is_module_installed


# TODO: Remove this class once hdmf-zarr is integrated into hdmf and the Zarr
# backend stops being an optional dependency.
class _MissingHdmfZarrError(ModuleNotFoundError):
    """Raised when a Zarr-backed file is encountered but ``hdmf-zarr`` is not installed.

    Subclassing ``ModuleNotFoundError`` lets external callers still do
    ``except ModuleNotFoundError:`` while keeping a narrow handle for the inspector
    to intercept only this specific failure (and not unrelated import errors raised
    elsewhere in the inspection pipeline).
    """


# Backward-compatible mapping of backend name to IO class. Kept for external callers
# that imported ``BACKEND_IO_CLASSES`` from ``nwbinspector.tools``. Internally the
# inspector now delegates to ``pynwb.read_nwb``; this mapping is no longer used here.
BACKEND_IO_CLASSES = {"hdf5": NWBHDF5IO}
if is_module_installed("hdmf_zarr"):
    from hdmf_zarr import NWBZarrIO

    BACKEND_IO_CLASSES["zarr"] = NWBZarrIO


def _get_method(path: str) -> Literal["local", "fsspec"]:
    if path.startswith(("https://", "http://", "s3://")):
        return "fsspec"
    elif Path(path).exists():
        return "local"
    else:
        message = (
            f"Unable to automatically determine method. Path {path} does not appear to be a URL and is not a file on "
            f"the local filesystem."
        )
        raise ValueError(message)


def _init_fsspec(path: str) -> "fsspec.AbstractFileSystem":  # type: ignore
    import fsspec

    if path.startswith(("https://", "http://")):
        return fsspec.filesystem("http")
    elif path.startswith("s3://"):
        return fsspec.filesystem("s3", anon=True)
    else:
        message = f"Unable to initialize fsspec on path '{path}'."
        raise ValueError(message)


def read_nwbfile_and_io(
    nwbfile_path: Union[str, Path],
    method: Optional[Literal["local", "fsspec", "ros3"]] = None,
    backend: Optional[Literal["hdf5", "zarr"]] = None,
) -> tuple[NWBFile, HDMFIO]:
    """
    Read an NWB file using the specified (or auto-detected) method, returning both the file and its IO object.

    For local files, backend detection (HDF5 vs Zarr) is delegated to ``pynwb.read_nwb``,
    which raises a helpful error when the file is a Zarr store but ``hdmf-zarr`` is not installed.
    Streaming via ``fsspec`` or ``ros3`` is HDF5-only.

    Parameters
    ----------
    nwbfile_path : str or pathlib.Path
        Path to the file on your system.
    method : "local", "fsspec", "ros3", or None (default)
        Where to read the file from; a local disk drive or streaming from an https:// or s3:// path.
        The default auto-detects based on the form of the path.
    backend : "hdf5", "zarr", or None (default)
        Deprecated. Backend selection is now handled automatically by ``pynwb.read_nwb`` for local
        files. The argument is accepted but ignored. Will be removed after 12/1/2026.

    Returns
    -------
    nwbfile : pynwb.NWBFile
        The in-memory NWBFile object.
    io : hdmf.backends.io.HDMFIO
        The initialized HDMFIO object used to read the file.
    """
    # TODO: remove the `backend` parameter after 12/1/2026
    if backend is not None:
        warn(
            "The `backend` argument is deprecated and will be removed after 12/1/2026. "
            "Backend selection is now handled automatically by `pynwb.read_nwb` for local files; "
            "remove the `backend=` argument from your call.",
            category=DeprecationWarning,
            stacklevel=2,
        )

    nwbfile_path = str(nwbfile_path)
    method = method or _get_method(nwbfile_path)

    if method != "local" and Path(nwbfile_path).exists():
        raise ValueError(
            f"The file ({nwbfile_path}) is a local path on your system, but the method ({method}) was selected! "
            "Please set method='local'."
        )
    if method == "local" and any(protocol in nwbfile_path for protocol in ["s3://", "https://"]):
        raise ValueError(
            f"The path ({nwbfile_path}) is an external URL, but the method (local) was selected! "
            "Please set method='fsspec' or 'ros3' (for HDF5 only)."
        )
    if method == "ros3" and nwbfile_path.startswith("s3://"):
        raise ValueError(
            "The ROS3 method was selected, but the URL starts with 's3://'! Please switch to an 'https://' URL."
        )

    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")

    if method == "local":
        if nwbfile_path.endswith(".nwb.zarr") and not is_module_installed("hdmf_zarr"):
            raise _MissingHdmfZarrError(
                f"Reading the Zarr-backed NWB file at '{nwbfile_path}' requires the 'hdmf-zarr' package.\n"
                "Install it with `pip install nwbinspector[zarr]` or `pip install hdmf-zarr`."
            )
        nwbfile = read_nwb(path=nwbfile_path)
        return nwbfile, nwbfile.get_read_io()

    # Streaming paths below are HDF5-only.
    io_kwargs: dict = dict(mode="r", load_namespaces=True)
    if method == "fsspec":
        fs = _init_fsspec(nwbfile_path)
        file = h5py.File(fs.open(nwbfile_path, "rb"))
        io_kwargs.update(file=file)
    else:  # ros3
        io_kwargs.update(path=nwbfile_path, driver="ros3")
    io = NWBHDF5IO(**io_kwargs)
    return io.read(), io


def read_nwbfile(
    nwbfile_path: Union[str, Path],
    method: Optional[Literal["local", "fsspec", "ros3"]] = None,
    backend: Optional[Literal["hdf5", "zarr"]] = None,
) -> NWBFile:
    """
    Read an NWB file using the specified (or auto-detected) method.

    Thin wrapper around ``read_nwbfile_and_io`` that returns only the NWBFile.
    See ``read_nwbfile_and_io`` for parameter and behavior details, including the
    deprecated ``backend`` argument.

    Returns
    -------
    nwbfile : pynwb.NWBFile
        The in-memory NWBFile object.
    """
    nwbfile, _ = read_nwbfile_and_io(nwbfile_path=nwbfile_path, method=method, backend=backend)
    return nwbfile
