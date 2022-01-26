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

    def add_dataset_to_nwb_container(self, file: h5py.File, gb_size: float):
        dataset = file.create_dataset(
            name="test_dataset",
            data=np.zeros(shape=int(gb_size * 1e9 / np.dtype("float").itemsize)),
        )
        nwb_container = NWBContainer(name="test_container")
        nwb_container.fields.update(dataset=dataset)
        return nwb_container

    def test_check_dataset_compression_below_default_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.5)
            self.assertDictEqual(
                d1=check_dataset_compression(nwb_container=nwb_container),
                d2=dict(severity="low", message="Consider enabling compression when writing a large dataset."),
            )

    def test_check_dataset_compression_above_default_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=2.0)
            self.assertDictEqual(
                d1=check_dataset_compression(nwb_container=nwb_container),
                d2=dict(severity="high", message="Consider enabling compression when writing a large dataset."),
            )

    def test_check_dataset_compression_below_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.25)
            self.assertDictEqual(
                d1=check_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.5),
                d2=dict(severity="low", message="Consider enabling compression when writing a large dataset."),
            )

    def test_check_dataset_compression_above_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.75)
            self.assertDictEqual(
                d1=check_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.5),
                d2=dict(severity="high", message="Consider enabling compression when writing a large dataset."),
            )
