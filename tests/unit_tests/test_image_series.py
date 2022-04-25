from unittest import TestCase
from tempfile import mkdtemp
from shutil import rmtree
from pathlib import Path

import numpy as np
from pynwb import NWBHDF5IO
from pynwb.image import ImageSeries

from nwbinspector import (
    InspectorMessage,
    Importance,
    check_image_series_external_file_valid,
    check_image_series_external_file_relative,
)
from nwbinspector.tools import make_minimal_nwbfile


class TestExternalFileValid(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.tempfile = self.tempdir / "tempfile.mov"
        self.nested_tempdir_2 = self.tempdir / "nested_dir"
        self.nested_tempdir_2.mkdir(parents=True)
        self.tempfile2 = self.nested_tempdir_2 / "tempfile2.avi"
        for file in [self.tempfile, self.tempfile2]:
            with open(file=file, mode="w") as fp:
                fp.write("Not a movie file, but at least it exists.")
        self.nwbfile = make_minimal_nwbfile()
        self.nwbfile.add_acquisition(
            ImageSeries(
                name="TestImageSeries",
                rate=1.0,
                external_file=[
                    "/".join([".", self.tempfile.name]),
                    "/".join([".", self.tempfile2.parent.stem, self.tempfile2.name]),
                ],
            )
        )
        self.nwbfile.add_acquisition(
            ImageSeries(
                name="TestImageSeriesBad1",
                rate=1.0,
                external_file=["madeup_file.mp4"],
            )
        )
        self.absolute_file_path = str(Path("madeup_file.mp4").absolute())
        self.nwbfile.add_acquisition(
            ImageSeries(name="TestImageSeriesBad2", rate=1.0, external_file=[self.absolute_file_path])
        )
        image_module = self.nwbfile.create_processing_module(name="behavior", description="testing imageseries")
        image_module.add(ImageSeries(name="TestImageSeries2", rate=1.0, external_file=[self.tempfile, self.tempfile2]))
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="w") as io:
            io.write(self.nwbfile)

    def tearDown(self):
        rmtree(self.tempdir)

    def test_check_image_series_external_file_valid_pass(self):
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="r") as io:
            nwbfile = io.read()
            assert check_image_series_external_file_valid(image_series=nwbfile.acquisition["TestImageSeries"]) is None

    def test_check_image_series_external_file_valid_bytestring_pass(self):
        """Can't call the io.write() step in setUp as that decodes the bytes with our version of h5py."""
        nwbfile = make_minimal_nwbfile()
        nwbfile.add_acquisition(
            ImageSeries(
                name="TestImageSeries",
                rate=1.0,
                external_file=[bytes("/".join([".", self.tempfile.name]), "utf-8")],
            )
        )
        assert check_image_series_external_file_relative(image_series=nwbfile.acquisition["TestImageSeries"]) is None

    def test_check_image_series_external_file_valid(self):
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["TestImageSeriesBad1"]
            assert check_image_series_external_file_valid(image_series=image_series)[0] == InspectorMessage(
                message=(
                    "The external file 'madeup_file.mp4' does not exist. Please confirm the relative location to the"
                    " NWBFile."
                ),
                importance=Importance.CRITICAL,
                check_function_name="check_image_series_external_file_valid",
                object_type="ImageSeries",
                object_name="TestImageSeriesBad1",
                location="/acquisition/TestImageSeriesBad1",
            )

    def test_check_image_series_external_file_relative_pass(self):
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="r") as io:
            nwbfile = io.read()
            assert (
                check_image_series_external_file_relative(image_series=nwbfile.acquisition["TestImageSeries"]) is None
            )

    def test_check_image_series_external_file_relative_bytestring_pass(self):
        """Can't call the io.write() step in setUp as that decodes the bytes with our version of h5py."""
        image_series = ImageSeries(
            name="TestImageSeries",
            rate=1.0,
            external_file=[bytes("/".join([".", self.tempfile.name]), "utf-8")],
        )
        assert check_image_series_external_file_relative(image_series=image_series) is None

    def test_check_image_series_external_file_relative(self):
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["TestImageSeriesBad2"]
            assert check_image_series_external_file_relative(image_series=image_series)[0] == InspectorMessage(
                message=(
                    f"The external file '{self.absolute_file_path}' is not a relative path. "
                    "Please adjust the absolute path to be relative to the location of the NWBFile."
                ),
                importance=Importance.BEST_PRACTICE_VIOLATION,
                check_function_name="check_image_series_external_file_relative",
                object_type="ImageSeries",
                object_name="TestImageSeriesBad2",
                location="/acquisition/TestImageSeriesBad2",
            )


def test_check_image_series_external_file_valid_pass_non_external():
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, data=np.zeros(shape=(3, 3, 3, 3)), unit="TestUnit")
    assert check_image_series_external_file_valid(image_series=image_series) is None
