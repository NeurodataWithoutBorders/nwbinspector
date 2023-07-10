"""Temporary tests for thorough testing and evaluation of the propsed `read_nwbfile` helper function."""
from pathlib import Path

import zarr
from hdmf.backends.io import HDMFIO
from hdmf_zarr import NWBZarrIO
from pynwb import NWBHDF5IO
from pynwb.testing.mock.file import mock_NWBFile
from pynwb.testing.mock.base import mock_TimeSeries

from nwbinspector.tools.testing import TemporaryFolderTestCase
from nwbinspector.tools import read_nwbfile


class TestReadNWB(TemporaryFolderTestCase):
    nwbfile_path: Path  # Define how to name and write the in-memory cls.nwbfile object to disk for each backend

    @classmethod
    def setUpClass(cls):
        cls.nwbfile = mock_NWBFile()
        cls.nwbfile.add_acquisition(mock_TimeSeries())

    def check_io_open(self, io: HDMFIO):
        """
        Please define this method for each separate backe-end as there may be separate strategies used.

        The check should assert that behavior is 'normal' (data can be accessed, other operations can be called
        on the I/O, etc.)
        """
        raise NotImplementedError("Please implement the `check_file_open` method!")

    def check_io_closed(self, io: HDMFIO):
        """
        Please define this method for each separate backe-end as there may be separate strategies used.

        The check should read the NWB file at the specified path using the `read_nwbfile` function, assert that
        behavior is 'normal' (data can be accessed, other operations can be called on the I/O, etc.) and then close
        the I/O and assert that the same behavior now results in an error.
        """
        raise NotImplementedError("Please implement the `check_file_closed` method!")

    def test_explicit_closure(self):
        nwbfile = read_nwbfile(path=self.nwbfile_path)
        self.check_io_open(io=nwbfile.read_io)

        nwbfile.read_io.close()
        self.check_io_closed(io=nwbfile.read_io)

    def test_object_deletion_closure(self):
        nwbfile = read_nwbfile(path=self.nwbfile_path)
        io = nwbfile.read_io  # keep reference in namespace so it persists after nwbfile deletion
        self.check_io_open(io=io)

        del nwbfile
        self.check_io_closed(io=io)

    def test_object_replacement_closure(self):
        nwbfile_1 = read_nwbfile(path=self.nwbfile_path)
        io_1 = nwbfile_1.read_io
        self.check_io_open(io=io_1)

        nwbfile_2 = read_nwbfile(path=self.nwbfile_path)
        io_2 = nwbfile_2.read_io
        self.check_io_open(io=io_2)

        nwbfile_2 = nwbfile_1
        self.check_io_closed(io=io_2)
        self.check_io_open(io=io_1)


class TestReadNWBHDF5(TestReadNWB):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.nwbfile_path = cls.temporary_folder / "test_read_nwbfile_hdf5.nwb"
        with NWBHDF5IO(path=cls.nwbfile_path, mode="w") as io:
            io.write(cls.nwbfile)

    def check_io_open(self, io: HDMFIO):
        """For HDF5, the file is 'open' if we can access data from slicing one of its `h5py.Dataset` objects."""
        assert io._file["acquisition"]["TimeSeries"]["data"][:2] is not None

    def check_io_closed(self, io: HDMFIO):
        """For HDF5, the file is 'closed' if attempts to access data from one of its `h5py.Dataset` result in error."""
        try:
            io._file["acquisition"]["TimeSeries"]["data"][:2]
            assert False, "The test to close the HDF5 I/O through manual closure of `nwbfile.read_io.close()` failed!"
        except ValueError as exception:
            assert exception.message == "Invalid location identifier (invalid location identifier)"


class TestReadNWBZarr(TestReadNWB):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.nwbfile_path = cls.temporary_folder / "test_read_nwbfile_zarr.nwb"
        with NWBZarrIO(path=cls.nwbfile_path, mode="w") as io:
            io.write(cls.nwbfile)

    def check_io_open(self, io: HDMFIO):
        """For Zarr, the private attribute `_ZarrIO__file` is set to a `zarr.group` on open."""
        assert isinstance(io._ZarrIO__file, zarr.Group)

    def check_io_closed(self, io: HDMFIO):
        """For Zarr, the private attribute `_ZarrIO__file` is replaced with `None` after closure."""
        assert io._ZarrIO__file is None
