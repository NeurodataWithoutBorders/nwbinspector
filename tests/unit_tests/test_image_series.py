import os
import unittest
from pathlib import Path
from shutil import rmtree
from tempfile import mkdtemp

import av
import numpy as np
from pynwb import NWBHDF5IO, H5DataIO
from pynwb.device import Device, DeviceModel
from pynwb.image import ImageSeries
from pynwb.ophys import ImagingPlane, OpticalChannel, TwoPhotonSeries

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_image_series_data_size,
    check_image_series_external_file_format,
    check_image_series_external_file_relative,
    check_image_series_external_file_valid,
    check_image_series_starting_frame_without_external_file,
    check_timestamps_match_first_dimension,
)
from nwbinspector.testing import make_minimal_nwbfile

TESTING_FILES_FOLDER_PATH = os.environ.get("TESTING_FILES_FOLDER_PATH", None)


def _write_video(path, codec, pixel_format):
    """Write a five frame 64 by 64 video so that a real codec can be read back from it."""
    with av.open(str(path), "w") as container:
        stream = container.add_stream(codec, rate=10)
        stream.width, stream.height, stream.pix_fmt = 64, 64, pixel_format
        for frame_index in range(5):
            array = np.full(shape=(64, 64, 3), fill_value=frame_index * 20, dtype=np.uint8)
            for packet in stream.encode(av.VideoFrame.from_ndarray(array, format="rgb24")):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)


@unittest.skipIf(
    TESTING_FILES_FOLDER_PATH is None,
    reason=(
        "These ImageSeries unit tests were skipped because the environment variable "
        "'TESTING_FILES_FOLDER_PATH' was not set!"
    ),
)
class TestExternalFileValid(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.testing_file = Path(TESTING_FILES_FOLDER_PATH) / "image_series_testing_file.nwb"

        assert cls.testing_file.exists()

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
            format="external",
            num_samples=1,
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


def test_check_image_series_starting_frame_without_external_file_pass_no_external_no_starting():
    """Test that an ImageSeries without external_file and without starting_frame passes."""
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, data=np.zeros(shape=(3, 3, 3, 3)), unit="TestUnit")
    assert check_image_series_starting_frame_without_external_file(image_series=image_series) is None


def test_check_image_series_starting_frame_without_external_file_pass_with_external():
    """Test that an ImageSeries with external_file passes regardless of starting_frame."""
    # Build a valid ImageSeries, then set the external attributes post-construction to avoid
    # construction-time validation (newer PyNWB requires num_samples for external series timed by rate).
    image_series = ImageSeries(
        name="TestImageSeries",
        rate=1.0,
        data=np.zeros(shape=(3, 3, 3, 3)),
        unit="TestUnit",
    )
    image_series.external_file = ["test.mp4"]
    image_series.starting_frame = [0]
    image_series.fields["data"] = None  # mimic a real external series (data is read-only, so null it directly)
    assert check_image_series_starting_frame_without_external_file(image_series=image_series) is None


def test_check_image_series_starting_frame_without_external_file_trigger():
    """Test that an ImageSeries with starting_frame but no external_file triggers."""
    # Create ImageSeries with external_file first, then modify
    image_series = ImageSeries(
        name="TestImageSeries",
        rate=1.0,
        data=np.zeros(shape=(3, 3, 3, 3)),
        unit="TestUnit",
    )
    # Manually set starting_frame to simulate a legacy file
    image_series.starting_frame = [0]

    result = check_image_series_starting_frame_without_external_file(image_series=image_series)
    expected_message = InspectorMessage(
        importance=Importance.BEST_PRACTICE_VIOLATION,
        message="ImageSeries has starting_frame set but no external_file. "
        "starting_frame is only relevant when using external files.",
        check_function_name="check_image_series_starting_frame_without_external_file",
        object_type="ImageSeries",
        object_name="TestImageSeries",
        location="/",
    )
    assert result == expected_message


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


class TestExternalFileFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = Path(mkdtemp())
        for file_name, codec, pixel_format in [
            ("h264.mp4", "libx264", "yuv420p"),
            ("vp9.webm", "libvpx-vp9", "yuv420p"),
            ("h264.mkv", "libx264", "yuv420p"),
            ("mjpeg.avi", "mjpeg", "yuvj420p"),
            ("ffv1.mkv", "ffv1", "yuv420p"),
            ("rawvideo.avi", "rawvideo", "yuv420p"),
        ]:
            _write_video(path=cls.tmpdir / file_name, codec=codec, pixel_format=pixel_format)

        cls.nwbfile_path = cls.tmpdir / "test.nwb"
        nwbfile = make_minimal_nwbfile()
        for series_name, file_name in [
            ("StandardMP4", "h264.mp4"),
            ("StandardWebM", "vp9.webm"),
            ("LegacyContainer", "h264.mkv"),
            ("LegacyCodec", "mjpeg.avi"),
            ("Lossless", "ffv1.mkv"),
            ("Uncompressed", "rawvideo.avi"),
            ("Missing", "missing.mp4"),
        ]:
            nwbfile.add_acquisition(
                ImageSeries(
                    name=series_name,
                    rate=1.0,
                    external_file=[f"./{file_name}"],
                    format="external",
                    num_samples=1,
                )
            )
        with NWBHDF5IO(path=cls.nwbfile_path, mode="w") as io:
            io.write(nwbfile)

    @classmethod
    def tearDownClass(cls):
        rmtree(cls.tmpdir)

    def setUp(self):
        self.io = NWBHDF5IO(path=self.nwbfile_path, mode="r")
        self.nwbfile = self.io.read()

    def tearDown(self):
        self.io.close()

    def test_standard_container_and_codec_passes(self):
        assert check_image_series_external_file_format(image_series=self.nwbfile.acquisition["StandardMP4"]) is None
        assert check_image_series_external_file_format(image_series=self.nwbfile.acquisition["StandardWebM"]) is None

    def test_lossy_codec_in_legacy_container(self):
        """The codec is H.264, so the container can be changed without re-encoding."""
        messages = check_image_series_external_file_format(image_series=self.nwbfile.acquisition["LegacyContainer"])

        assert len(messages) == 1
        assert messages[0] == InspectorMessage(
            message=(
                "The external file './h264.mkv' uses the '.mkv' container, which is not a standard "
                "container for sharing video. Please use MP4 or WebM instead. The codec is already a "
                "recommended one, so the container can be changed without re-encoding: "
                "ffmpeg -i ./h264.mkv -c copy output.mp4"
            ),
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            check_function_name="check_image_series_external_file_format",
            object_type="ImageSeries",
            object_name="LegacyContainer",
            location="/acquisition/LegacyContainer",
        )

    def test_legacy_codec(self):
        """A re-encoding settles the container as well, so the container is not reported separately."""
        messages = check_image_series_external_file_format(image_series=self.nwbfile.acquisition["LegacyCodec"])

        assert len(messages) == 1
        assert messages[0].message == (
            "The external file './mjpeg.avi' uses the 'mjpeg' codec, which is not one of the standard "
            "video codecs. Please use H.264, VP8, VP9 or AV1 in an MP4 or WebM container, or FFV1 if the "
            "video has to stay lossless. Note that H.264 is covered by patents while VP8, VP9 and AV1 are "
            "royalty-free."
        )

    def test_lossless_codec_passes(self):
        """The container of a lossless video is not reported, so FFV1 passes whatever holds it."""
        assert check_image_series_external_file_format(image_series=self.nwbfile.acquisition["Lossless"]) is None

    def test_uncompressed_codec(self):
        messages = check_image_series_external_file_format(image_series=self.nwbfile.acquisition["Uncompressed"])

        assert len(messages) == 1
        assert "'rawvideo' codec" in messages[0].message

    def test_missing_file_is_ignored(self):
        """A missing external file is already reported by check_image_series_external_file_valid."""
        assert check_image_series_external_file_format(image_series=self.nwbfile.acquisition["Missing"]) is None

    def test_two_photon_series_is_ignored(self):
        """The external file of a TwoPhotonSeries is imaging data, such as a TIFF stack, rather than video."""
        device_model = DeviceModel(name="Model", description="microscope model", manufacturer="Manufacturer")
        imaging_plane = ImagingPlane(
            name="ImagingPlane",
            optical_channel=OpticalChannel(
                name="OpticalChannel", description="an optical channel", emission_lambda=500.0
            ),
            description="an imaging plane",
            device=Device(name="Microscope", description="a microscope", model=device_model),
            excitation_lambda=600.0,
            indicator="GFP",
            location="V1",
        )
        two_photon_series = TwoPhotonSeries(
            name="TwoPhotonSeries",
            imaging_plane=imaging_plane,
            rate=1.0,
            external_file=["./frames.tif"],
            format="external",
            num_samples=1,
            unit="n.a.",
        )

        assert check_image_series_external_file_format(image_series=two_photon_series) is None
