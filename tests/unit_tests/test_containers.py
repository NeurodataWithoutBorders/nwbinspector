import numpy as np
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree
from unittest import TestCase

import h5py
from pynwb import NWBContainer

from nwbinspector import check_dataset_compression, Importance
from nwbinspector.register_checks import Severity, InspectorMessage


class TestNWBContainers(TestCase):
    def setUp(self):
        self.test_folder = Path(mkdtemp())
        self.file_path = str(self.test_folder / "test_file.nwb")

    def tearDown(self):
        rmtree(self.test_folder)

    @staticmethod
    def add_dataset_to_nwb_container(file: h5py.File, gb_size: float):
        dataset = file.create_dataset(
            name="test_dataset",
            data=np.zeros(shape=int(gb_size * 1e9 / np.dtype("float").itemsize)),
        )
        nwb_container = NWBContainer(name="test_container")
        nwb_container.fields.update(dataset=dataset)
        return nwb_container

    def test_check_dataset_compression_below_default_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.1)
            assert check_dataset_compression(nwb_container=nwb_container) is None

    def test_check_dataset_compression_above_default_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=1.1)
            true_output = InspectorMessage(
                severity=Severity.NO_SEVERITY,
                message="test_dataset is large and not compressed. Consider enabling compression when writing a large "
                        "dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_dataset_compression",
                object_type="NWBContainer",
                object_name="test_container",
                location="/",
            )
            self.assertEqual(first=check_dataset_compression(nwb_container=nwb_container), second=true_output)

    def test_check_dataset_compression_below_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.1)
            assert check_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.15) is None

    def test_check_dataset_compression_above_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.2)
            true_output = InspectorMessage(
                severity=Severity.NO_SEVERITY,
                message="test_dataset is large and not compressed. Consider enabling compression when writing a large "
                        "dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_dataset_compression",
                object_type="NWBContainer",
                object_name="test_container",
                location="/",
            )
            self.assertEqual(
                first=check_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.15),
                second=true_output,
            )
