"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector.check_time_series import (
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
)


class TestTimeSeriesChecks(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )
        device = self.nwbfile.create_device(name="test_device")
        electrode_group = self.nwbfile.create_electrode_group(
            name="test_group", description="", location="", device=device
        )
        self.num_electrodes = 4
        electrode_ids = list(range(self.num_electrodes))
        for id in electrode_ids:
            self.nwbfile.add_electrode(
                id=id,
                x=np.nan,
                y=np.nan,
                z=np.nan,
                imp=np.nan,
                location="",
                filtering="",
                group=electrode_group,
            )
        self.electrode_table_region = self.nwbfile.create_electrode_table_region(
            electrode_ids, description=""
        )

    def tearDown(self):
        rmtree(self.tempdir)

    def test_check_dataset_compression(self):
        n_bytes = 3e6
        # itemsize of 8 because of float dtype
        n_frames = int(n_bytes / (self.num_electrodes * 8))
        ephys_ts = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys",
            data=np.zeros(shape=(n_frames, self.num_electrodes)),
            electrodes=self.electrode_table_region,
            rate=10.0,
        )
        self.nwbfile.add_acquisition(ephys_ts)

        nwbfile_path = str(self.tempdir / "testing.nwb")
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            nwbfile_in = io.read()
            output_message = check_dataset_compression(
                time_series=nwbfile_in.acquisition["test_ecephys"]
            )
            self.assertEqual(
                first=output_message,
                second="Consider enabling compression when writing a large dataset.",
            )

    def test_check_regular_timestamps(self):
        time_series = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys",
            data=np.zeros(shape=(3, self.num_electrodes)),
            electrodes=self.electrode_table_region,
            timestamps=[1.2, 3.2, 5.2],
        )
        self.nwbfile.add_acquisition(time_series)

        true_message = (
            f"The TimeSeries '{time_series.name}' has a constant sampling rate. "
            f"Consider specifying starting_time={time_series.timestamps[0]} "
            f"and rate={time_series.timestamps[1] - time_series.timestamps[0]} instead of timestamps."
        )
        output_message_1 = check_regular_timestamps(
            time_series=self.nwbfile.acquisition["test_ecephys"]
        )
        self.assertEqual(first=output_message_1, second=true_message)

        nwbfile_path = str(self.tempdir / "testing.nwb")
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            nwbfile_in = io.read()
            output_message_2 = check_regular_timestamps(
                time_series=nwbfile_in.acquisition["test_ecephys"]
            )
            self.assertEqual(first=output_message_2, second=true_message)

    def test_check_data_orientation(self):
        pass
