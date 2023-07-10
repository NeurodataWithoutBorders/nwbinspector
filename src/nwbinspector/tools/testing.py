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
