"""Authors: Cody Baker and Ben Dichter."""
import pynwb
import hdmf
from hdmf.testing import TestCase

from nwbinspector.register_checks import register_check


class TestUtils(TestCase):
    def assertFunctionInChecks(self, check_function, available_checks):
        function_names = [x.__name__ for x in available_checks]
        self.assertIn(member=check_function.__name__, container=function_names)

    def test_decorator_importance(self):
        from nwbinspector import available_checks, importance_levels

        neurodata_type = hdmf.common.DynamicTable
        for importance in importance_levels:

            @register_check(importance=importance, neurodata_type=neurodata_type)
            def good_check_function():
                pass

            self.assertFunctionInChecks(
                check_function=good_check_function, available_checks=available_checks[importance][neurodata_type]
            )

    def test_decorator_multiple_data_objects_same_type(self):
        from nwbinspector import available_checks

        importance = "Best Practice Violation"
        neurodata_type = hdmf.common.DynamicTable

        @register_check(importance=importance, neurodata_type=neurodata_type)
        def good_check_function_1():
            pass

            self.assertFunctionInChecks(
                check_function=good_check_function_1, available_checks=available_checks[importance][neurodata_type]
            )

        @register_check(importance=importance, neurodata_type=neurodata_type)
        def good_check_function_2():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_2, available_checks=available_checks[importance][neurodata_type]
        )

    def test_decorator_multiple_data_objects_different_type(self):
        from nwbinspector import available_checks

        importance = "Best Practice Suggestion"
        neurodata_type_1 = hdmf.common.DynamicTable
        neurodata_type_2 = pynwb.TimeSeries

        @register_check(importance=importance, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_1, available_checks=available_checks[importance][neurodata_type_1]
        )

        @register_check(importance=importance, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_2, available_checks=available_checks[importance][neurodata_type_2]
        )

    def test_decorator_importance_error(self):
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
