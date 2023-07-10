"""Temporary tests for thorough testing and evaluation of the propsed `read_nwbfile` helper function."""
from nwbinspector.tools.testing import TemporaryFolderTestCase
from nwbinspector.tools import read_nwbfile

class TestReadNWB(TemporaryFolderTestCase):
    @classmethod
    def setUpClass(cls):
        cls.nwbfile = None  # TODO: make in-memory NWBFile with mock time series
        cls.hdf5_nwbfile_path = cls.temporary_folder / "test_read_nwbfile_hdf5.nwb"
        cls.zarr_nwbfile_path = cls.temporary_folder / "test_read_nwbfile_zarr.nwb"
        
        # TODO: save same in-memory file to each path
        
    def test_hdf5_explicit_closure(self):
        nwbfile = read_nwbfile(path=self.hdf5_nwbfile_path)
        assert nwbfile.acquisition["TimeSeries"].data[:] is not None  # would fail if I/O had closed automatically
        nwbfile.read_io.close()
        try:
            nwbfile.acquisition["TimeSeries"].data[:]
            assert False, "The test to close the I/O through manual closure of `nwbfile.read_io.close()` failed!"
        except ValueError as exception:
            assert exception.message == ""
