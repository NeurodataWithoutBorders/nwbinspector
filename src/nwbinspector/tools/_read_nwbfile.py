"""Temporary module for thorough testing and evaluation of the propsed `read_nwbfile` helper function."""
from pathlib import Path
from warnings import filterwarnings

from typing import Optional, Literal

import h5py
from hdmf_zarr import NWBZarrIO
from pynwb import NWBHDF5IO, NWBFile

_backend_io_classes = dict(hdf5=NWBHDF5IO, zarr=NWBZarrIO)


def _get_method(path: str):
    if path.startswith(("https://", "http://", "s3://")):
        return "fsspec"
    elif Path(path).is_file():
        return "local"
    else:
        raise ValueError(
            f"Unable to automatically determine method. Path {path} does not appear to be a URL and is not a file on "
            f"the local filesystem.")


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

    if len(possible_backends) > 1:
        raise ValueError("more than one possible backend found: {possible_backends}")
    elif len(possible_backends) == 0:
        raise ValueError("No possible backend found.")

    return possible_backends[0]


def read_nwbfile(
    nwbfile_path: str,
    mode: str = "r",
    method: Optional[Literal["local", "fsspec", "ros3"]] = None,
    backend: Optional[Literal["hdf5", "zarr"]] = None
) -> NWBFile:
    method = method or _get_method(nwbfile_path)
    backend = backend or _get_backend(nwbfile_path, method)

    # Filter out some of most common warnings that don't really matter with `load_namespaces=True`
    filterwarnings(action="ignore", message="No cached namespaces found in .*")
    filterwarnings(action="ignore", message="Ignoring cached namespace .*")
    if method == "fsspec":
        fs = _init_fsspec(nwbfile_path)
        f = fs.open(nwbfile_path, "rb")
        file = h5py.File(f)
        io = _backend_io_classes[backend](file=file, mode=mode, load_namespaces=True)
    else:
        io = _backend_io_classes[backend](
            path=nwbfile_path, mode=mode, load_namespaces=True, driver="ros3" if method == "ros3" else None
        )
    nwbfile = io.read()
    # nwbfile.io = io  # Should not be necessary when using HDMF PR #882

    return nwbfile
