"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree
from unittest import TestCase

import h5py
from pynwb import NWBContainer

from nwbinspector import check_dataset_compression


class TestNWBContainers(TestCase):
    def setUp(self):
        self.test_folder = Path(mkdtemp())
        self.file_path = str(self.test_folder / "test_file.nwb")

    def tearDown(self):
        rmtree(self.test_folder)

    def add_dataset_to_nwb_container(self, file: h5py.File, n_bytes: int):
        dataset = file.create_dataset(
            name="test_dataset",
            data=np.zeros(shape=int(n_bytes / np.dtype("float").itemsize)),
        )
        nwb_container = NWBContainer(name="test_container")
        nwb_container.fields.update(dataset=dataset)
        return nwb_container

    def test_check_dataset_compression_below_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, n_bytes=1e6)
            self.assertIsNone(
                obj=check_dataset_compression(nwb_container=nwb_container)
            )

    def test_check_dataset_compression_above_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, n_bytes=3e6)
            self.assertEqual(
                first=check_dataset_compression(nwb_container=nwb_container),
                second="Consider enabling compression when writing a large dataset.",
            )
