from datetime import datetime
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

import h5py
import numpy as np
from pynwb import NWBContainer, NWBFile
from pynwb.image import ImageSeries

from nwbinspector import Importance, InspectorMessage, Severity
from nwbinspector.checks import (
    check_empty_string_for_optional_attribute,
    check_large_dataset_compression,
    check_single_chunk_dataset,
    check_small_dataset_compression,
)


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

    def test_check_small_dataset_compression_below_default_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.1)
            true_output = InspectorMessage(
                message="test_dataset is not compressed. Consider enabling compression when writing a dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_small_dataset_compression",
                object_type="NWBContainer",
                object_name="test_container",
                location="/",
            )
            self.assertEqual(first=check_small_dataset_compression(nwb_container=nwb_container), second=true_output)

    def test_check_small_dataset_compression_below_50MB(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.001)
            self.assertIsNone(obj=check_large_dataset_compression(nwb_container=nwb_container))

    def test_check_small_dataset_compression_below_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.1)
            true_output = InspectorMessage(
                message="test_dataset is not compressed. Consider enabling compression when writing a dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_small_dataset_compression",
                object_type="NWBContainer",
                object_name="test_container",
                location="/",
            )
            self.assertEqual(
                first=check_small_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.15),
                second=true_output,
            )

    def test_check_small_dataset_compression_above_manual_threshold(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.2)
            true_output = InspectorMessage(
                severity=Severity.HIGH,
                message="test_dataset is not compressed. Consider enabling compression when writing a dataset.",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="check_small_dataset_compression",
                object_type="NWBContainer",
                object_name="test_container",
                location="/",
            )
            self.assertEqual(
                first=check_small_dataset_compression(nwb_container=nwb_container, gb_severity_threshold=0.15),
                second=true_output,
            )

    def test_check_large_dataset_compression_below_20GB(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, gb_size=0.001)
            self.assertIsNone(obj=check_large_dataset_compression(nwb_container=nwb_container))


def test_no_error_raised_when_dataset_is_compressed():
    """Test that no InspectorMessage is returned for a compressed dataset."""
    test_folder = Path(mkdtemp())
    file_path = test_folder / "temp_test_file.nwb"

    with h5py.File(name=str(file_path), mode="w") as file:
        data = np.zeros(shape=(100, 100, 100))  # example small data shape
        dataset = file.create_dataset(name="test_dataset", data=data, compression="gzip")  # Enable compression

        nwb_container = NWBContainer(name="test_container")
        nwb_container.fields.update(dataset=dataset)

        # Use a very low lower bound to simulate a large dataset threshold without a huge dataset
        result = check_large_dataset_compression(nwb_container=nwb_container, gb_lower_bound=0.0001)

        assert result is None

    # Cleanup the temporary directory after the test
    rmtree(test_folder)


def test_hit_check_empty_string_for_optional_attribute():
    nwbfile = NWBFile(
        session_description="aa", identifier="aa", session_start_time=datetime.now().astimezone(), pharmacology=""
    )

    assert check_empty_string_for_optional_attribute(nwb_container=nwbfile)[0] == InspectorMessage(
        message='The attribute "pharmacology" is optional and you have supplied an empty string. Improve by omitting '
        "this attribute (in MatNWB or PyNWB) or entering as None (in PyNWB)",
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        location="/",
        object_type="NWBFile",
        object_name="root",
        check_function_name="check_empty_string_for_optional_attribute",
    )


def test_miss_check_empty_string_for_optional_attribute():
    nwbfile = NWBFile(session_description="aa", identifier="aa", session_start_time=datetime.now().astimezone())
    assert check_empty_string_for_optional_attribute(nwb_container=nwbfile) is None


def test_check_empty_string_for_optional_attribute_skip_non_string():
    image_series = ImageSeries(
        name="TestImageSeries",
        description="Behavior video of animal moving in environment",
        unit="n.a.",
        external_file=["test1.mp4", "test2.avi"],
        format="external",
        starting_frame=[0, 2],
        timestamps=[0.0, 0.04, 0.07, 0.1, 0.14, 0.16, 0.21],
    )  # The `data` field will be created by PyNWB but it will be empty and will otherwise raise warning/error via numpy
    assert check_empty_string_for_optional_attribute(nwb_container=image_series) is None


class TestSingleChunkDataset(TestCase):
    def setUp(self):
        self.test_folder = Path(mkdtemp())
        self.file_path = str(self.test_folder / "test_file.nwb")

    def tearDown(self):
        rmtree(self.test_folder)

    @staticmethod
    def add_dataset_to_nwb_container(file: h5py.File, **dataset_kwargs):
        dataset = file.create_dataset(name="test_dataset", **dataset_kwargs)
        nwb_container = NWBContainer(name="test_container")
        nwb_container.fields.update(dataset=dataset)
        return nwb_container

    def test_small_single_chunk_suggests_contiguous(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, shape=(10,), dtype="float64", chunks=(10,))
            self.assertEqual(
                first=check_single_chunk_dataset(nwb_container=nwb_container),
                second=InspectorMessage(
                    message=(
                        "test_dataset is stored as a single uncompressed chunk. Contiguous storage would be a better "
                        "fit for a dataset of this size."
                    ),
                    importance=Importance.BEST_PRACTICE_SUGGESTION,
                    check_function_name="check_single_chunk_dataset",
                    object_type="NWBContainer",
                    object_name="test_container",
                    location="/",
                ),
            )

    def test_large_single_chunk_suggests_chunking_and_compression(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, shape=(10,), dtype="float64", chunks=(10,))
            self.assertEqual(
                first=check_single_chunk_dataset(nwb_container=nwb_container, mb_lower_bound=0.00008),
                second=InspectorMessage(
                    message=(
                        "test_dataset is stored as a single uncompressed chunk. Split it into several chunks and "
                        "enable compression."
                    ),
                    importance=Importance.BEST_PRACTICE_SUGGESTION,
                    check_function_name="check_single_chunk_dataset",
                    object_type="NWBContainer",
                    object_name="test_container",
                    location="/",
                ),
            )

    def test_small_resizable_dataset_passes(self):
        """Contiguous storage is not available to a resizable dataset, so a small one is left alone."""
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(
                file=file, shape=(10, 3), dtype="float64", chunks=(64, 3), maxshape=(None, 3)
            )
            self.assertIsNone(obj=check_single_chunk_dataset(nwb_container=nwb_container))

    def test_large_resizable_dataset_suggests_chunking_and_compression(self):
        """Above the threshold the advice is to split and compress, which a resizable dataset can follow."""
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(
                file=file, shape=(10, 3), dtype="float64", chunks=(64, 3), maxshape=(None, 3)
            )
            message = check_single_chunk_dataset(nwb_container=nwb_container, mb_lower_bound=0)
            self.assertIn(member="Split it into several chunks and enable compression.", container=message.message)

    def test_contiguous_dataset_passes(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, shape=(10,), dtype="float64")
            self.assertIsNone(obj=check_single_chunk_dataset(nwb_container=nwb_container))

    def test_compressed_single_chunk_passes(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(
                file=file, shape=(10,), dtype="float64", chunks=(10,), compression="gzip"
            )
            self.assertIsNone(obj=check_single_chunk_dataset(nwb_container=nwb_container))

    def test_multiple_chunks_pass(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(file=file, shape=(10, 3), dtype="float64", chunks=(5, 3))
            self.assertIsNone(obj=check_single_chunk_dataset(nwb_container=nwb_container))

    def test_empty_dataset_passes(self):
        with h5py.File(name=self.file_path, mode="w") as file:
            nwb_container = self.add_dataset_to_nwb_container(
                file=file, shape=(0,), dtype="float64", chunks=(1024,), maxshape=(None,)
            )
            self.assertIsNone(obj=check_single_chunk_dataset(nwb_container=nwb_container))
