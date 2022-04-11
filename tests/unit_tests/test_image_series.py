from unittest import TestCase
from tempfile import mkdtemp
from shutil import rmtree
from pathlib import Path

import numpy as np
from pynwb.image import ImageSeries

from nwbinspector.checks.image_series import check_image_series_external_file_valid
from nwbinspector.register_checks import InspectorMessage, Importance


class TestExternalFileValid(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.tempfile = self.tempdir / "tempfile.mov"
        with open(file=self.tempfile, mode="w") as fp:
            fp.write("Not a movie file, but at least it exists.")

    def tearDown(self):
        rmtree(self.tempdir)

    def test_check_image_series_external_file_valid_pass(self):
        image_series = ImageSeries(name="TestImageSeries", rate=1.0, external_file=[self.tempfile])
        assert check_image_series_external_file_valid(image_series=image_series) is None


def test_check_image_series_external_file_valid_pass_non_external():
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, data=np.zeros(shape=(3, 3, 3, 3)), unit="TestUnit")
    assert check_image_series_external_file_valid(image_series=image_series) is None


def test_check_image_series_external_file_valid():
    image_series = ImageSeries(name="TestImageSeries", rate=1.0, external_file=["madeup_file.mov"])
    assert check_image_series_external_file_valid(image_series=image_series)[0] == InspectorMessage(
        message="The external file does not exist. Please confirm the relative location to the NWBFile.",
        importance=Importance.CRITICAL,
        check_function_name="check_image_series_external_file_valid",
        object_type="ImageSeries",
        object_name="TestImageSeries",
        location="/",
    )
