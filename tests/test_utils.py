"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import hdmf
from hdmf.testing import TestCase

from nwbinspector.utils import add_to_default_checks, check_regular_series


class TestUtils(TestCase):
    def test_decorator_severities(self):
        from nwbinspector.utils import default_checks

        severities = [1, 2, 3]
        neurodata_type = hdmf.common.DynamicTable
        for severity in severities:

            @add_to_default_checks(severity=severity, neurodata_type=neurodata_type)
            def good_check_function():
                pass

            self.assertIn(
                member=good_check_function,
                container=default_checks[severity][neurodata_type],
            )

    def test_decorator_multiple_data_objects_same_type(self):
        from nwbinspector.utils import default_checks

        severity = 2
        neurodata_type = hdmf.common.DynamicTable

        @add_to_default_checks(severity=severity, neurodata_type=neurodata_type)
        def good_check_function_1():
            pass

        self.assertIn(
            member=good_check_function_1,
            container=default_checks[severity][neurodata_type],
        )

        @add_to_default_checks(severity=severity, neurodata_type=neurodata_type)
        def good_check_function_2():
            pass

        self.assertIn(
            member=good_check_function_2,
            container=default_checks[severity][neurodata_type],
        )

    def test_decorator_multiple_data_objects_different_type(self):
        from nwbinspector.utils import default_checks

        severity = 2
        neurodata_type_1 = hdmf.common.DynamicTable
        neurodata_type_2 = pynwb.TimeSeries

        @add_to_default_checks(severity=severity, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        self.assertIn(
            member=good_check_function_1,
            container=default_checks[severity][neurodata_type_1],
        )

        @add_to_default_checks(severity=severity, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        self.assertIn(
            member=good_check_function_2,
            container=default_checks[severity][neurodata_type_2],
        )

    def test_decorator_severity_error(self):
        bad_severity = 4
        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated severity ({bad_severity}) of custom check (bad_severity_function) is not in range of 1-3."
            ),
        ):

            @add_to_default_checks(severity=bad_severity, neurodata_type=None)
            def bad_severity_function():
                pass

    def test_check_regular_series(self):
        self.assertTrue(check_regular_series(series=[1, 2, 3]))
        self.assertFalse(check_regular_series(series=[1, 2, 4]))
