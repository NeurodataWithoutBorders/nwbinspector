from unittest import TestCase
from tempfile import mkdtemp
from shutil import rmtree
from pathlib import Path

import numpy as np
from pynwb import NWBHDF5IO
from pynwb.image import ImageSeries

from nwbinspector.tools import make_minimal_nwbfile
from nwbinspector.checks.image_series import check_image_series_external_file_valid
from nwbinspector.register_checks import InspectorMessage, Importance


class TestExternalFileValid(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.tempfile = self.tempdir / "tempfile.mov"
        self.nested_tempdir_2 = self.tempdir / "nested_dir"
        self.nested_tempdir_2.mkdir(parents=True)
        self.tempfile2 = self.nested_tempdir_2 / "tempfile2.avi"
        with open(file=self.tempfile, mode="w") as fp:
            fp.write("Not a movie file, but at least it exists.")
        self.nwbfile = make_minimal_nwbfile()
        self.nwbfile.add_acquisition(
            ImageSeries(name="TestImageSeries", rate=1.0, external_file=[self.tempfile, self.tempfile2])
        )
        self.nwbfile.add_acquisition(
            ImageSeries(name="TestImageSeriesBad", rate=1.0, external_file=["madeup_file.mp4"])
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

    def test_check_image_series_external_file_valid(self):
        with NWBHDF5IO(path=self.tempdir / "tempnwbfile.nwb", mode="r") as io:
            nwbfile = io.read()
            image_series = nwbfile.acquisition["TestImageSeriesBad"]
            print(check_image_series_external_file_valid(image_series=image_series)[0])
            assert check_image_series_external_file_valid(image_series=image_series)[0] == InspectorMessage(
                message="The external file does not exist. Please confirm the relative location to the NWBFile.",
                importance=Importance.CRITICAL,
                check_function_name="check_image_series_external_file_valid",
                object_type="ImageSeries",
                object_name="TestImageSeriesBad",
                location="/acquisition/TestImageSeriesBad",
            )


def test_check_image_series_external_file_valid_pass_non_external():
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, data=np.zeros(shape=(3, 3, 3, 3)), unit="TestUnit")
    assert check_image_series_external_file_valid(image_series=image_series) is None
