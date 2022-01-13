"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector import check_dataset_compression


class PostWriteIntegrationTestTimeSeriesChecks(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )
        self.nwbfile_path = str(self.tempdir / "testing.nwb")

    def tearDown(self):
        rmtree(self.tempdir)

    def assertPostWriteCheck(self, check_function, true_message: str):
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)
        with pynwb.NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            written_nwbfile = io.read()
            self.assertEqual(
                first=check_function(
                    nwb_container=written_nwbfile.acquisition["test_time_series"]
                ),
                second=true_message,
            )

    def test_check_dataset_compression(self):
        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_unit",
            data=np.zeros(shape=int(3e6 / np.dtype("float").itemsize)),
            rate=1.0,
        )
        self.nwbfile.add_acquisition(time_series)
        self.assertPostWriteCheck(
            check_function=check_dataset_compression,
            true_message="Consider enabling compression when writing a large dataset.",
        )
