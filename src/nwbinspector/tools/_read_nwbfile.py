"""Temporary module for thorough testing and evaluation of the propsed `read_nwbfile` helper function."""
from pathlib import Path
from warnings import filterwarnings
from typing import Optional, Literal, Union

import h5py
from hdmf_zarr import NWBZarrIO
from pynwb import NWBHDF5IO, NWBFile

_backend_io_classes = dict(hdf5=NWBHDF5IO, zarr=NWBZarrIO)


def _get_method(path: str):
    if path.startswith(("https://", "http://", "s3://")):
        return "fsspec"
    elif Path(path).exists():
        return "local"
    else:
        raise ValueError(
            f"Unable to automatically determine method. Path {path} does not appear to be a URL and is not a file on "
            f"the local filesystem."
        )


def _init_fsspec(path):
    import fsspec

    if path.startswith(("https://", "http://")):
        return fsspec.filesystem("http")
    elif path.startswith("s3://"):
        return fsspec.filesystem("s3", anon=True)


def _get_backend(path: str, method: Literal["local", "fsspec", "ros3"]):
    if method == "ros3":
        return "hdf5"

    possible_backends = []
    if method == "fsspec":
        fs = _init_fsspec(path)
        with fs.open(path, "rb") as f:
            for backend, cls in _backend_io_classes.items():
                if cls.can_read(f):
                    possible_backends.append(backend)
    else:
        for backend, cls in _backend_io_classes.items():
            if cls.can_read(path):
                possible_backends.append(backend)

    if len(possible_backends) > 1:  # pragma: no cover
        raise ValueError(
            f"More than one possible backend found - please choose from the following: {possible_backends}"
        )
    elif len(possible_backends) == 0:
        raise ValueError("No compatible backend found.")

    return possible_backends[0]


def read_nwbfile(
    nwbfile_path: Union[str, Path],
    method: Optional[Literal["local", "fsspec", "ros3"]] = None,
    backend: Optional[Literal["hdf5", "zarr"]] = None,
) -> NWBFile:
    """
    Read an NWB file using the specified (or auto-detected) method and specified (or auto-detected) backend.

    Parameters
    ----------
    nwbfile_path : string or pathlib.Path
        Path to the file on your system.
    method : "local", "fsspec", "ros3", or None (default)
        Where to read the file from; a local disk drive or steaming from an https:// or s3:// path.
        The default auto-detects based on the form of the path.
        When streaming, the default method is "fsspec".
        Note that "ros3" is specific to HDF5 backend files.
    backend : "hdf5", "zarr", or None (default)
        Type of backend used to write the file.
        The default auto-detects the type of the file.

    Returns
    -------
    pynwb.NWBFile
    """
    nwbfile_path = str(nwbfile_path)  # If pathlib.Path, cast to str; if already str, no harm done
    method = method or _get_method(nwbfile_path)
    backend = backend or _get_backend(nwbfile_path, method)

    # Filter out some of most common warnings that don't really matter with `load_namespaces=True`
    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")
    io_kwargs = dict(mode="r", load_namespaces=True)
    if method == "fsspec":
        fs = _init_fsspec(nwbfile_path)
        f = fs.open(nwbfile_path, "rb")
        file = h5py.File(f)
        io_kwargs.update(file=file)
    else:
        io_kwargs.update(path=nwbfile_path)
    if method == "ros3":
        io_kwargs.update(driver="ros3")
    io = _backend_io_classes[backend](**io_kwargs)
    nwbfile = io.read()

    return nwbfile
