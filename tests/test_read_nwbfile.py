"""Temporary tests for thorough testing and evaluation of the propsed `read_nwbfile` helper function."""
from pathlib import Path

import zarr
import pytest
from hdmf.backends.io import HDMFIO
from hdmf_zarr import NWBZarrIO
from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.base import mock_TimeSeries

from nwbinspector.tools import read_nwbfile


@pytest.fixture(scope='session')
def hdf5_nwbfile_path(tmpdir_factory):
    nwbfile_path = tmpdir_factory.mktemp('data').join("test_read_nwbfile_hdf5.nwb")
    if not Path(nwbfile_path).exists():
        nwbfile = mock_NWBFile()
        nwbfile.add_acquisition(mock_TimeSeries())
        with NWBHDF5IO(path=str(nwbfile_path), mode="w") as io:
            io.write(nwbfile)
    return nwbfile_path


@pytest.fixture(scope='session')
def zarr_nwbfile_path(tmpdir_factory):
    nwbfile_path = tmpdir_factory.mktemp('data').join("test_read_nwbfile_zarr.nwb")
    if not Path(nwbfile_path).exists():
        nwbfile = mock_NWBFile()
        nwbfile.add_acquisition(mock_TimeSeries())
        with NWBZarrIO(path=str(nwbfile_path), mode="w") as io:
            io.write(nwbfile)
    return nwbfile_path


# HDF5 assertion styles
def check_hdf5_io_open(io: HDMFIO):
    """For HDF5, the file is 'open' if we can access data from slicing one of its `h5py.Dataset` objects."""
    assert io._file["acquisition"]["TimeSeries"]["data"][:2] is not None


def check_hdf5_io_closed(io: HDMFIO):
    """For HDF5, the file is 'closed' if attempts to access data from one of its `h5py.Dataset` result in error."""
    try:
        io._file["acquisition"]["TimeSeries"]["data"][:2]
        assert False, "The test to close the HDF5 I/O failed!"  # The line above should throw a ValueError
    except ValueError as exception:
        assert str(exception) == "Invalid location identifier (invalid location identifier)"


# Zarr assert styles
def check_zarr_io_open(io: HDMFIO):
    """For Zarr, the private attribute `_ZarrIO__file` is set to a `zarr.group` on open."""
    assert isinstance(io._ZarrIO__file, zarr.Group)


def check_zarr_io_closed(io: HDMFIO):
    """For Zarr, the private attribute `_ZarrIO__file` is replaced with `None` after closure."""
    assert io._ZarrIO__file is None


# HDF5 tests
def test_hdf5_explicit_closure(hdf5_nwbfile_path):
    nwbfile = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_hdf5_io_closed(io=nwbfile.read_io)


def test_hdf5_object_deletion_closure(hdf5_nwbfile_path):
    nwbfile = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io = nwbfile.read_io  # keep reference in namespace so it persists after nwbfile deletion
    check_hdf5_io_open(io=io)

    del nwbfile
    check_hdf5_io_closed(io=io)


def test_hdf5_object_replacement_closure(hdf5_nwbfile_path):
    nwbfile_1 = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io_1 = nwbfile_1.read_io
    check_hdf5_io_open(io=io_1)

    nwbfile_2 = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io_2 = nwbfile_2.read_io
    check_hdf5_io_open(io=io_2)

    nwbfile_2 = nwbfile_1
    check_hdf5_io_closed(io=io_2)
    check_hdf5_io_open(io=io_1)


# # Zarr tests
def test_zarr_explicit_closure(zarr_nwbfile_path):
    nwbfile = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    check_zarr_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_zarr_io_closed(io=nwbfile.read_io)


def test_zarr_object_deletion_closure(zarr_nwbfile_path):
    nwbfile = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io = nwbfile.read_io  # keep reference in namespace so it persists after nwbfile deletion
    check_zarr_io_open(io=io)

    del nwbfile
    check_zarr_io_closed(io=io)


def test_zarr_object_replacement_closure(zarr_nwbfile_path):
    nwbfile_1 = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io_1 = nwbfile_1.read_io
    check_zarr_io_open(io=io_1)

    nwbfile_2 = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io_2 = nwbfile_2.read_io
    check_zarr_io_open(io=io_2)

    nwbfile_2 = nwbfile_1
    check_zarr_io_closed(io=io_2)
    check_zarr_io_open(io=io_1)
