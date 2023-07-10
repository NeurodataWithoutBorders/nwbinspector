"""Helper functions for internal use in the test suite that rely on external dependencies (i.e., pynwb)."""
from uuid import uuid4
from datetime import datetime
from typing import Optional, Tuple
from urllib import request
from shutil import rmtree
from warnings import warn
from tempfile import mkdtemp

import h5py
from pynwb import NWBFile
from hdmf.testing import TestCase as HDMFTestCase


def make_minimal_nwbfile():
    """Most basic NWBFile that can exist."""
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())


def check_streaming_enabled() -> Tuple[bool, Optional[str]]:
    """
    General purpose helper for determining if the environment can support S3 DANDI streaming.

    Returns the boolean status of the check and, if False, provides a string reason for the failure for the user to
    utilize as they please (raise an error or warning with that message, print it, or ignore it).
    """
    try:
        request.urlopen("https://dandiarchive.s3.amazonaws.com/ros3test.nwb", timeout=1)
    except request.URLError:
        return False, "Internet access to DANDI failed."
    if "ros3" not in h5py.registered_drivers():
        return False, "ROS3 driver not installed."
    return True, None


class TemporaryFolderTestCase(HDMFTestCase):
    @classmethod
    def setUpClass(cls):
        """
        The `tmpdir` pytest fixture does not immediately clean itself up after running the test suite.

        Instead it caches some number of total testing runs under a temporary folder.

        This helper defines a simple class attribute `temporary_folder` which is then cleaned up when the test are done.
        """
        cls.temporary_folder = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        """Note that this cleanup is only attempted and not guaranteed to succeed on stuck I/O; mostly on Windows."""
        try:
            rmtree(cls.temporary_folder)
        except PermissionError:  # pragma: no cover
            warn(f"Unable to clean up the temporary folder {cls.temporary_folder}!")
