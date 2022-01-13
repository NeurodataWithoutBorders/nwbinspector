"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from collections import defaultdict
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector.refactor_inspector import inspect_nwb


class TestInspector(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now().astimezone(),
        )

    def tearDown(self):
        rmtree(self.tempdir)

    def add_big_dataset_no_compression(self):
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

        n_bytes = 3e6
        # itemsize of 8 because of float dtype
        n_frames = int(n_bytes / (self.num_electrodes * 8))
        ephys_data = np.zeros(shape=(n_frames, self.num_electrodes))
        ephys_ts = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_1",
            data=ephys_data,
            electrodes=self.electrode_table_region,
            rate=10.0,
        )
        self.nwbfile.add_acquisition(ephys_ts)

    def add_regular_timestamps(self):
        time_series = pynwb.ecephys.ElectricalSeries(
            name="test_ecephys_2",
            data=np.zeros(shape=(5, self.num_electrodes)),
            electrodes=self.electrode_table_region,
            timestamps=np.arange(1.2, 11.2, 2.0),
        )
        self.nwbfile.add_acquisition(time_series)

    def test_inspect_nwb(self):
        self.add_big_dataset_no_compression()
        self.add_regular_timestamps()

        nwbfile_path = str(self.tempdir / "testing.nwb")
        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
            io.write(self.nwbfile)

        with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
            nwbfile_in = io.read()
            check_results = inspect_nwb(nwbfile=nwbfile_in)

            regular_timestamp_series = nwbfile_in.acquisition["test_ecephys_2"]
            regular_timestamp_rate = (
                regular_timestamp_series.timestamps[1]
                - regular_timestamp_series.timestamps[0]
            )
            print(check_results)
            true_results = defaultdict(
                list,
                {
                    1: [
                        dict(
                            check_function_name="check_dataset_compression",
                            object_type="ElectricalSeries",
                            object_name="test_ecephys_1",
                            output="Consider enabling compression when writing a large dataset.",
                        )
                    ],
                    2: [
                        dict(
                            check_function_name="check_regular_timestamps",
                            object_type="ElectricalSeries",
                            object_name="test_ecephys_2",
                            output=(
                                f"The {type(regular_timestamp_series).__name__} '{regular_timestamp_series.name}' "
                                "has a constant sampling rate. Consider specifying "
                                f"starting_time={regular_timestamp_series.timestamps[0]} and "
                                f"rate={regular_timestamp_rate} instead of timestamps."
                            ),
                        )
                    ],
                },
            )
            self.assertDictEqual(d1=check_results, d2=true_results)
