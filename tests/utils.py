"""Helper functions for all testing modules."""
from pynwb import NWBFile

from uuid import uuid4
from datetime import datetime


def make_minimal_nwbfile():
    """Most basic NWBFile that can exist."""
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())
