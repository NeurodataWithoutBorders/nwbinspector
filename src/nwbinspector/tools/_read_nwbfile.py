"""Temporary module for thorough testing and evaluation of the proposed `read_nwbfile` helper function."""

from pathlib import Path
from typing import Literal, Optional, Union
from warnings import filterwarnings

import h5py
from hdmf.backends.io import HDMFIO
from hdmf_zarr import NWBZarrIO
from pynwb import NWBHDF5IO, NWBFile

BACKEND_IO_CLASSES = dict(
    hdf5=NWBHDF5IO,
    zarr=NWBZarrIO,
)


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
        fs = _init_fsspec(path=path)
        with fs.open(path=path, mode="rb") as file:
            for backend_name, backend_class in BACKEND_IO_CLASSES.items():
                if backend_class.can_read(path=file):
                    possible_backends.append(backend_name)
    else:
        for backend_name, backend_class in BACKEND_IO_CLASSES.items():
            if backend_class.can_read(path):
                possible_backends.append(backend_name)

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
    return_io: bool = False,
) -> Union[NWBFile, tuple[NWBFile, HDMFIO]]:
    """
    Read an NWB file using the specified (or auto-detected) method and specified (or auto-detected) backend.

    Parameters
    ----------
    nwbfile_path : str or pathlib.Path
        Path to the file on your system.
    method : "local", "fsspec", "ros3", or None (default)
        Where to read the file from; a local disk drive or steaming from an https:// or s3:// path.
        The default auto-detects based on the form of the path.
        When streaming, the default method is "fsspec".
        Note that "ros3" is specific to HDF5 backend files.
    backend : "hdf5", "zarr", or None (default)
        Type of backend used to write the file.
        The default auto-detects the type of the file.
    return_io : bool, default: False
        Whether to return the HDMFIO object used to open the file.

    Returns
    -------
    nwbfile : pynwb.NWBFile
        The in-memory NWBFile object.
    io : hdmf.backends.io.HDMFIO, optional
        Only passed if `return_io` is True.
        The initialized HDMFIO object used to read the file.
    """
    nwbfile_path = str(nwbfile_path)  # If pathlib.Path, cast to str; if already str, no harm done

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

    backend = backend or _get_backend(nwbfile_path, method)
    if method == "local" and not BACKEND_IO_CLASSES[  # Temporary until .can_read() is able to work on streamed bytes
        backend
    ].can_read(path=nwbfile_path):
        raise IOError(f"The chosen backend ({backend}) is unable to read the file! Please select a different backend.")

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
    io = BACKEND_IO_CLASSES[backend](**io_kwargs)
    nwbfile = io.read()

    if return_io:
        return (nwbfile, io)
    else:  # Note: do not be concerned about io object closing due to garbage collection here
        return nwbfile  # (it is attached as an attribute to the NWBFile object)
