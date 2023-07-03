from hdmf import DataIO
from hdmf_zarr import NWBZarrIO
from pynwb import NWBFile, NWBHDF5IO
from pynwb.testing.mock import mock_NWBFile, mock_TimeSeries
from nwbinspector import read_nwbfile
from nwbinspector.testing import ReadNWBFileTestCase, ReadNWBFileReplacementClosesTestCase

class ReadNWBFileBasicGenerator(ReadNWBFileTestCase):
    data_io: DataIO

    @classmethod
    def setUpClass(cls):
        self.nwbfile_path = tmpdir / f"test_read_nwbfile_{data_io.__class__.name}.nwb"

        nwbfile = mock_NWBFile()
        nwbfile.add_acquisition(mock_TimeSeries())
        with self.data_io(path=self.nwbfile_path, mode="w") as io:
            io.write(nwbfile)

    @classmethod
    def tearDownClass(cls):
        """Pytest fixture 'tmpdir' does not automatically clean itself up."""
        self.nwbfile_path.unlink() 

class ReadNWBFileReplacementBasicGenerator(ReadNWBFileReplacementClosesTestCase):
    data_io: DataIO

    @classmethod
    def setUpClass(cls):
        self.nwbfile_path_1 = tmpdir / f"test_read_nwbfile_{data_io.__class__.name}_replacement_1.nwb"
        self.nwbfile_path_2 = tmpdir / f"test_read_nwbfile_{data_io.__class__.name}_replacement_2.nwb"

        nwbfile_1 = mock_NWBFile()
        nwbfile_1.add_acquisition(mock_TimeSeries())
        with self.data_io(path=self.nwbfile_path_1, mode="w") as io:
            io.write(nwbfile_1)

        nwbfile_2 = mock_NWBFile()
        nwbfile_2.add_acquisition(mock_TimeSeries())
        with self.data_io(path=self.nwbfile_path_2, mode="w") as io:
            io.write(nwbfile_2)

    @classmethod
    def tearDownClass(cls):
        """Pytest fixture 'tmpdir' does not automatically clean itself up."""
        self.nwbfile_path_1.unlink()
        self.nwbfile_path_2.unlink()

# mark as optional, streaming enabled/disabled
class ReadNWBFileFromDANDI(ReadNWBFileTestCase):
    dandiset_id: str
    dandiset_file_path: str

    @classmethod
    def setUpClass(cls):
        s3_asset = lookup_from_dandi_file_and_dandiset
        self.nwbfile_path = s3_asset

class TestReadNWBFileHDF5Backend(ReadNWBFileBasicGenerator):
    data_io = NWBHDF5IO

class TestReadNWBFileZarrBackend(ReadNWBFileBasicGenerator):
    data_io = NWBZarrIO

class TestReadNWBFileHDF5Backend(ReadNWBFileReplacementBasicGenerator):
    data_io = NWBHDF5IO

class TestReadNWBFileZarrBackend(ReadNWBFileReplacementBasicGenerator):
    data_io = NWBZarrIO

class HDF5StreamingTest1(ReadNWBFileFromDANDI):
    dandiset_id = "000350"
    dandiset_file_path = "sub-asd/sub-asd_ses-asd.nwb"

# TODO, maybe with staging for now?
#class ZarrStreamingTest1(ReadNWBFileFromDANDI):
#    dandiset_id = "000350"