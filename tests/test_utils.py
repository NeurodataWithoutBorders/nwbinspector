"""Authors: Cody Baker and Ben Dichter."""
from shutil import rmtree
from tempfile import mkdtemp
from uuid import uuid4
from datetime import datetime
from pathlib import Path

import pynwb
import h5py
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

    def test_decorator_severities(self):
        from nwbinspector.utils import default_checks

        severities = [1, 2, 3]
        data_object = h5py.Dataset
        for severity in severities:

            @add_to_default_checks(severity=severity, data_object=data_object)
            def good_check_function():
                pass

            self.assertIn(
                member=good_check_function,
                container=default_checks[severity][data_object],
            )

    def test_decorator_multiple_data_objects_same_type(self):
        from nwbinspector.utils import default_checks

        severity = 2
        data_object = h5py.Dataset

        @add_to_default_checks(severity=severity, data_object=data_object)
        def good_check_function_1():
            pass

        self.assertIn(
            member=good_check_function_1,
            container=default_checks[severity][data_object],
        )

        @add_to_default_checks(severity=severity, data_object=data_object)
        def good_check_function_2():
            pass

        self.assertIn(
            member=good_check_function_2,
            container=default_checks[severity][data_object],
        )

    def test_decorator_multiple_data_objects_different_type(self):
        from nwbinspector.utils import default_checks

        severity = 2
        data_object_1 = h5py.Dataset
        data_object_2 = pynwb.TimeSeries

        @add_to_default_checks(severity=severity, data_object=data_object_1)
        def good_check_function_1():
            pass

        self.assertIn(
            member=good_check_function_1,
            container=default_checks[severity][data_object_1],
        )

        @add_to_default_checks(severity=severity, data_object=data_object_2)
        def good_check_function_2():
            pass

        self.assertIn(
            member=good_check_function_2,
            container=default_checks[severity][data_object_2],
        )

    def test_decorator_severity_error(self):
        bad_severity = 4
        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated severity ({bad_severity}) of custom check (bad_severity_function) is not in range of 1-3."
            ),
        ):

            @add_to_default_checks(severity=bad_severity, data_object=None)
            def bad_severity_function():
                pass
