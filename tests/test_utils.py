"""Authors: Cody Baker and Ben Dichter."""
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb
from hdmf.testing import TestCase

from nwbinspector.utils import add_to_default_checks


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

    def test_decorator(self):
        from nwbinspector.utils import default_checks

        severities = [1, 2, 3]
        for severity in severities:

            @add_to_default_checks(severity=severity)
            def good_check_function():
                pass

            self.assertIn(
                member=good_check_function, container=default_checks[severity]
            )

    def test_decorator_severity_error(self):
        bad_severity = 4
        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated severity ({bad_severity}) of custom check (bad_severity_function) is not in range of 1-3."
            ),
        ):

            @add_to_default_checks(severity=bad_severity)
            def bad_severity_function():
                pass
