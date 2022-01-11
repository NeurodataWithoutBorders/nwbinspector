"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime

import pynwb

from nwbinspector import refactor_inspector


class TestInspectorFunctions(TestCase):
    def setUp(self):
        self.tempdir = mkdtemp()
        self.base_nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now(),
        )

    def tearDown(self):
        rmtree(self.tempdir)

    def test_check_dset_size(self):
        nwbfile = self.base_nwbfile
        device = nwbfile.create_device(name="test_device")
        electrode_group = nwbfile.create_electrode_group(
            name="test_group", description="", location="", device=device
        )
        num_electrodes = 4
        electrode_ids = list(range(num_electrodes))
        for id in electrode_ids:
            nwbfile.add_electrode(
                id=id,
                x=np.nan,
                y=np.nan,
                z=np.nan,
                imp=np.nan,
                location="",
                filtering="",
                group=electrode_group,
            )
        electrode_table_region = nwbfile.create_electrode_table_region(
            electrode_ids, description=""
        )

        n_bytes = 3e6
        # itemsize of 8 because of float dtype
        n_frames = int(n_bytes / (num_electrodes * 8))
        ephys_data = np.random.rand(n_frames, num_electrodes)
        ephys_ts = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys",
            data=ephys_data,
            electrodes=electrode_table_region,
            rate=10.0,
        )
        nwbfile.add_acquisition(ephys_ts)

        output_message = refactor_inspector.check_dset_size(
            obj=nwbfile.acquisition["test_ecephys"]
        )
        self.assertEqual(
            first=output_message,
            second=f"Consider enabling compression when writing a large dataset.",
        )
