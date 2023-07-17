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
from nwbinspector.testing import check_streaming_tests_enabled

STREAMING_TESTS_ENABLED, DISABLED_STREAMING_TESTS_REASON = check_streaming_tests_enabled()


@pytest.fixture(scope="session")
def hdf5_nwbfile_path(tmpdir_factory):
    nwbfile_path = tmpdir_factory.mktemp("data").join("test_read_nwbfile_hdf5.nwb")
    if not Path(nwbfile_path).exists():
        nwbfile = mock_NWBFile()
        nwbfile.add_acquisition(mock_TimeSeries())
        with NWBHDF5IO(path=str(nwbfile_path), mode="w") as io:
            io.write(nwbfile)
    return nwbfile_path


@pytest.fixture(scope="session")
def zarr_nwbfile_path(tmpdir_factory):
    nwbfile_path = tmpdir_factory.mktemp("data").join("test_read_nwbfile_zarr.nwb")
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


def test_hdf5_object_deletion_does_not_close_io(hdf5_nwbfile_path):
    """Deleting the `nwbfile` object should not trigger `io.close` if `io` is still being referenced independently."""
    nwbfile = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io = nwbfile.read_io  # keep reference in namespace so it persists after nwbfile deletion
    check_hdf5_io_open(io=io)

    del nwbfile
    check_hdf5_io_open(io=io)


def test_hdf5_object_replacement_does_not_close_io(hdf5_nwbfile_path):
    """Deleting the `nwbfile` object should not trigger `io.close` if `io` is still being referenced independently."""
    nwbfile_1 = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io_1 = nwbfile_1.read_io
    check_hdf5_io_open(io=io_1)

    nwbfile_2 = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
    io_2 = nwbfile_2.read_io
    check_hdf5_io_open(io=io_2)

    nwbfile_2 = nwbfile_1
    check_hdf5_io_open(io=io_1)
    check_hdf5_io_open(io=io_2)


# # Zarr tests
def test_zarr_explicit_closure(zarr_nwbfile_path):
    nwbfile = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    check_zarr_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_zarr_io_closed(io=nwbfile.read_io)


def test_zarr_object_deletion_does_not_close_io(zarr_nwbfile_path):
    """Deleting the `nwbfile` object should not trigger `io.close` if `io` is still being referenced independently."""
    nwbfile = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io = nwbfile.read_io  # keep reference in namespace so it persists after nwbfile deletion
    check_zarr_io_open(io=io)

    del nwbfile
    check_zarr_io_open(io=io)


def test_zarr_object_replacement_does_not_close_io(zarr_nwbfile_path):
    """Deleting the `nwbfile` object should not trigger `io.close` if `io` is still being referenced independently."""
    nwbfile_1 = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io_1 = nwbfile_1.read_io
    check_zarr_io_open(io=io_1)

    nwbfile_2 = read_nwbfile(nwbfile_path=zarr_nwbfile_path)
    io_2 = nwbfile_2.read_io
    check_zarr_io_open(io=io_2)

    nwbfile_2 = nwbfile_1
    check_zarr_io_open(io=io_1)
    check_zarr_io_open(io=io_2)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_fsspec_https():
    nwbfile = read_nwbfile(
        nwbfile_path="https://dandi-api-staging-dandisets.s3.amazonaws.com/blobs/6a6/1ba/6a61bab5-0662-49e5-be46-0b9ee9a27297",
        method="fsspec",
    )
    check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_hdf5_io_closed(io=nwbfile.read_io)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_fsspec_s3():
    nwbfile = read_nwbfile(
        nwbfile_path="s3://dandiarchive/blobs/6a6/1ba/6a61bab5-0662-49e5-be46-0b9ee9a27297",
        method="fsspec",
    )
    check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_hdf5_io_closed(io=nwbfile.read_io)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_ros3_https():
    nwbfile = read_nwbfile(
        nwbfile_path="https://dandi-api-staging-dandisets.s3.amazonaws.com/blobs/6a6/1ba/6a61bab5-0662-49e5-be46-0b9ee9a27297",
        method="ros3",
    )
    check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_hdf5_io_closed(io=nwbfile.read_io)


@pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
def test_hdf5_ros3_streaming_s3():
    nwbfile = read_nwbfile(
        nwbfile_path="s3://dandiarchive/blobs/6a6/1ba/6a61bab5-0662-49e5-be46-0b9ee9a27297",
        method="ros3",
    )
    check_hdf5_io_open(io=nwbfile.read_io)

    nwbfile.read_io.close()
    check_hdf5_io_closed(io=nwbfile.read_io)


# Zarr streaming WIP: see https://github.com/dandi/dandi-cli/issues/1310
# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_fsspec_streaming_https():
#     nwbfile = read_nwbfile(nwbfile_path="https://dandi-api-staging-dandisets.s3.amazonaws.com/blobs/6a6/1ba/6a61bab5-0662-49e5-be46-0b9ee9a27297")
#     check_hdf5_io_open(io=nwbfile.read_io)

#     nwbfile.read_io.close()
#     check_hdf5_io_closed(io=nwbfile.read_io)


# Zarr streaming WIP: see https://github.com/dandi/dandi-cli/issues/1310
# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_fsspec_streaming_s3():
#     nwbfile = read_nwbfile(nwbfile_path=hdf5_nwbfile_path)
#     check_hdf5_io_open(io=nwbfile.read_io)

#     nwbfile.read_io.close()
#     check_hdf5_io_closed(io=nwbfile.read_io)

# Zarr streaming WIP: see https://github.com/dandi/dandi-cli/issues/1310
# @pytest.mark.skipif(not STREAMING_TESTS_ENABLED, reason=DISABLED_STREAMING_TESTS_REASON or "")
# def test_zarr_ros3_error():
#     test that an error is raised with ros3 driver on zarr (not applicable)
