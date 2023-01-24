import unittest
from pathlib import Path
from tempfile import mkdtemp
from shutil import rmtree

import numpy as np
from pynwb import NWBHDF5IO, H5DataIO
from pynwb.image import ImageSeries

from nwbinspector import (
    InspectorMessage,
    Importance,
    check_image_series_external_file_valid,
    check_image_series_external_file_relative,
    check_image_series_data_size,
    check_timestamps_match_first_dimension,
)
from nwbinspector.tools import make_minimal_nwbfile
from nwbinspector.testing import load_testing_config

try:
    testing_config = load_testing_config()
    testing_file = Path(testing_config["LOCAL_PATH"]) / "image_series_testing_file.nwb"
    NO_CONFIG = False  # Depending on the method of installation, a config may not have generated
except FileNotFoundError:
    testing_file = "Not found"
    NO_CONFIG = True


@unittest.skipIf(
    NO_CONFIG or not testing_file.exists(),
    reason=f"The ImageSeries unit tests were skipped because the required file ({testing_file}) was not found!",
)
class TestExternalFileValid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        testing_config = load_testing_config()
        cls.testing_file = Path(testing_config["LOCAL_PATH"]) / "image_series_testing_file.nwb"

    def setUp(self):
        self.io = NWBHDF5IO(path=self.testing_file, mode="r")
        self.nwbfile = self.io.read()

    def tearDown(self):
        self.io.close()

    def test_check_image_series_external_file_valid_pass(self):
        assert (
            check_image_series_external_file_valid(
                image_series=self.nwbfile.acquisition["TestImageSeriesGoodExternalPaths"]
            )
            is None
        )

    def test_check_image_series_external_file_valid_bytestring_pass(self):
        """Can't use the NWB file since the call to io.write() decodes the bytes with modern versions of h5py."""
        good_external_path = Path(self.nwbfile.acquisition["TestImageSeriesGoodExternalPaths"].external_file[0])
        image_series = ImageSeries(
            name="TestImageSeries",
            rate=1.0,
            external_file=[bytes("/".join([".", good_external_path.name]), "utf-8")],
        )
        assert check_image_series_external_file_relative(image_series=image_series) is None

    def test_check_image_series_external_file_valid(self):
        with NWBHDF5IO(path=self.testing_file, mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["TestImageSeriesExternalPathDoesNotExist"]

            assert check_image_series_external_file_valid(image_series=image_series)[0] == InspectorMessage(
                message=(
                    "The external file 'madeup_file.mp4' does not exist. Please confirm the relative location to the"
                    " NWBFile."
                ),
                importance=Importance.CRITICAL,
                check_function_name="check_image_series_external_file_valid",
                object_type="ImageSeries",
                object_name="TestImageSeriesExternalPathDoesNotExist",
                location="/acquisition/TestImageSeriesExternalPathDoesNotExist",
            )

    def test_check_image_series_external_file_relative_pass(self):
        with NWBHDF5IO(path=self.testing_file, mode="r") as io:
            nwbfile = io.read()

            assert (
                check_image_series_external_file_relative(
                    image_series=nwbfile.acquisition["TestImageSeriesGoodExternalPaths"]
                )
                is None
            )

    def test_check_image_series_external_file_relative_trigger(self):
        with NWBHDF5IO(path=self.testing_file, mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["TestImageSeriesExternalPathIsNotRelative"]

            assert check_image_series_external_file_relative(image_series=image_series)[0] == InspectorMessage(
                message=(
                    f"The external file '{image_series.external_file[0]}' is not a relative path. "
                    "Please adjust the absolute path to be relative to the location of the NWBFile."
                ),
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_image_series_external_file_relative",
                object_type="ImageSeries",
                object_name="TestImageSeriesExternalPathIsNotRelative",
                location="/acquisition/TestImageSeriesExternalPathIsNotRelative",
            )


def test_check_image_series_external_file_valid_pass_non_external():
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, data=np.zeros(shape=(3, 3, 3, 3)), unit="TestUnit")

    assert check_image_series_external_file_valid(image_series=image_series) is None


def test_check_small_image_series_stored_internally():
    gb_size = 0.010  # 10 MB
    frame_length = 10
    total_elements = int(gb_size * 1e9 / np.dtype("float").itemsize) // (frame_length * frame_length)
    data = np.zeros(shape=(total_elements, frame_length, frame_length, 1))
    image_series = ImageSeries(name="ImageSeriesLarge", rate=1.0, data=data, unit="TestUnit")

    assert check_image_series_data_size(image_series=image_series) is None


def test_check_image_series_external_file_no_data_valid_pass():
    image_series = ImageSeries(
        name="ImageSeriesLarge",
        external_file=["Test"],
        format="external",
        timestamps=[0, 1, 2, 3],
        unit="TestUnit",
    )
    assert check_timestamps_match_first_dimension(time_series=image_series) is None


def test_check_large_image_series_stored_internally():
    gb_size = 0.010  # 10 MB
    frame_length = 10
    total_elements = int(gb_size * 1e9 / np.dtype("float").itemsize) // (frame_length * frame_length)
    data = np.zeros(shape=(total_elements, frame_length, frame_length, 1))
    image_series = ImageSeries(name="ImageSeriesLarge", rate=1.0, data=data, unit="TestUnit")
    gb_lower_bound = gb_size * 0.9
    inspector_message = check_image_series_data_size(image_series=image_series, gb_lower_bound=gb_lower_bound)

    expected_message = InspectorMessage(
        importance=Importance.BEST_PRACTICE_VIOLATION,
        message="ImageSeries is very large. Consider using external mode for better storage.",
        check_function_name="check_image_series_data_size",
        object_type="ImageSeries",
        object_name="ImageSeriesLarge",
        location="/",
    )

    assert inspector_message == expected_message


class TestCheckImageSeriesStoredInternally(unittest.TestCase):
    maxDiff = None

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = Path(mkdtemp())
        cls.nwbfile_path = cls.tmpdir / "test_compressed_image_series.nwb"
        cls.gb_size = 0.01  # 10 MB

        image_length = 10
        total_frames = int(cls.gb_size * 1e9 / np.dtype("float").itemsize) // (image_length * image_length)

        # Use random data in order to give non-trivial compression size
        # Fix the seed to give consistent result every run
        np.random.seed = 123
        dtype = "uint8"
        data = np.random.randint(
            low=0, high=np.iinfo(dtype).max, size=(total_frames, image_length, image_length, 1), dtype=dtype
        )
        image_series = ImageSeries(name="ImageSeries", rate=1.0, data=H5DataIO(data), unit="TestUnit")

        nwbfile = make_minimal_nwbfile()
        nwbfile.add_acquisition(image_series)

        with NWBHDF5IO(path=cls.nwbfile_path, mode="w") as io:
            io.write(nwbfile)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tmpdir)

    def test_check_image_series_stored_internally_compressed_larger_threshold(self):
        """With compression enabled, the size by the check should be less than the full uncompressed size."""
        with NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["ImageSeries"]

            assert check_image_series_data_size(image_series=image_series, gb_lower_bound=self.gb_size) is None

    def test_check_image_series_stored_internally_compressed_smaller_threshold(self):
        with NWBHDF5IO(path=self.nwbfile_path, mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["ImageSeries"]

            expected_message = InspectorMessage(
                importance=Importance.BEST_PRACTICE_VIOLATION,
                message="ImageSeries is very large. Consider using external mode for better storage.",
                check_function_name="check_image_series_data_size",
                object_type="ImageSeries",
                object_name="ImageSeries",
                location="/acquisition/ImageSeries",
            )

            assert (
                check_image_series_data_size(
                    image_series=image_series,
                    gb_lower_bound=self.gb_size / 10,  # Compression of uint8 noise is unlikely be more than 10:1 ratio
                )
                == expected_message
            )
