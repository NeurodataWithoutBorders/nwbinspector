"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from unittest import TestCase
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb

from nwbinspector.refactor_inspector import inspect_nwb


class TestInspectorFunctions(TestCase):
    def setUp(self):
        self.tempdir = Path(mkdtemp())
        self.base_nwbfile = pynwb.NWBFile(
            session_description="Testing inspector.",
            identifier=str(uuid4()),
            session_start_time=datetime.now(),
        )

    def tearDown(self):
        rmtree(self.tempdir)

    def test_inspect_nwb(self):
        pass
