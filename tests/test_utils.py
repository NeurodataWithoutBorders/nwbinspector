"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import hdmf
from hdmf.testing import TestCase

from nwbinspector.utils import register_check, check_regular_series


class TestUtils(TestCase):
    def test_decorator_severities(self):
        from nwbinspector import available_checks, importance_levels

        neurodata_type = hdmf.common.DynamicTable
        for importance in importance_levels:

            @register_check(importance=importance, neurodata_type=neurodata_type)
            def good_check_function():
                pass

            self.assertIn(member=good_check_function, container=available_checks[importance][neurodata_type])

    def test_decorator_multiple_data_objects_same_type(self):
        from nwbinspector import available_checks

        importance = "Best Practice Violation"
        neurodata_type = hdmf.common.DynamicTable

        @register_check(importance=importance, neurodata_type=neurodata_type)
        def good_check_function_1():
            pass

        self.assertIn(member=good_check_function_1, container=available_checks[importance][neurodata_type])

        @register_check(importance=importance, neurodata_type=neurodata_type)
        def good_check_function_2():
            pass

        self.assertIn(member=good_check_function_2, container=available_checks[importance][neurodata_type])

    def test_decorator_multiple_data_objects_different_type(self):
        from nwbinspector import available_checks

        importance = "Best Practice Suggestion"
        neurodata_type_1 = hdmf.common.DynamicTable
        neurodata_type_2 = pynwb.TimeSeries

        @register_check(importance=importance, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        self.assertIn(member=good_check_function_1, container=available_checks[importance][neurodata_type_1])

        @register_check(importance=importance, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        self.assertIn(member=good_check_function_2, container=available_checks[importance][neurodata_type_2])

    def test_decorator_severity_error(self):
        from nwbinspector import importance_levels

        bad_importance = "test_bad_importance"
        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated importance ({bad_importance}) of custom check (bad_severity_function) is not a valid "
                f"importance level! Please choose from {importance_levels}."
            ),
        ):

            @register_check(importance=bad_importance, neurodata_type=None)
            def bad_severity_function():
                pass

    def test_check_regular_series(self):
        self.assertTrue(check_regular_series(series=[1, 2, 3]))
        self.assertFalse(check_regular_series(series=[1, 2, 4]))
