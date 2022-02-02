"""Authors: Cody Baker and Ben Dichter."""
from platform import python_version
from packaging import version
from enum import Enum

from hdmf.common import DynamicTable
from pynwb import TimeSeries
from hdmf.testing import TestCase

from nwbinspector.register_checks import register_check, Importance, Severity


class TestRegisterClass(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_time_series = TimeSeries(name="temp", data=[], unit="", rate=1.0)

    def assertFunctionInChecks(self, check_function, available_checks):
        function_names = [x.__name__ for x in available_checks]
        self.assertIn(member=check_function.__name__, container=function_names)

    def test_register_importance_error_non_enum_type(self):
        bad_importance = "test_bad_importance"

        if version.parse(python_version()) >= version.parse("3.8"):
            with self.assertRaisesWith(
                exc_type=TypeError,
                exc_msg=f" unsupported operand type(s) for 'in': '{type({bad_importance})}' and 'EnumMeta'",
            ):

                @register_check(importance=bad_importance, neurodata_type=None)
                def bad_severity_function():
                    pass

        else:
            with self.assertRaisesWith(
                exc_type=ValueError,
                exc_msg=(
                    f"Indicated importance ({bad_importance}) of custom check (bad_severity_function) is not a valid "
                    "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                    "or Importance.BEST_PRACTICE_SUGGESTION."
                ),
            ):

                @register_check(importance=bad_importance, neurodata_type=None)
                def bad_severity_function():
                    pass

    def test_register_importance_error_enum_type(self):
        class SomeRandomEnum(Enum):
            random_name = -1

        bad_importance = SomeRandomEnum.random_name

        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated importance ({bad_importance}) of custom check (bad_severity_function) is not a valid "
                "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                "or Importance.BEST_PRACTICE_SUGGESTION."
            ),
        ):

            @register_check(importance=bad_importance, neurodata_type=None)
            def bad_severity_function():
                pass

    def test_register_severity_error_non_enum_type(self):
        bad_severity = "test_bad_severity"

        if version.parse(python_version()) >= version.parse("3.8"):
            with self.assertRaisesWith(
                exc_type=TypeError,
                exc_msg=f" unsupported operand type(s) for 'in': '{type({bad_severity})}' and 'EnumMeta'",
            ):

                @register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=None)
                def bad_severity_function():
                    return dict(severity=bad_severity)

        else:
            with self.assertRaisesWith(
                exc_type=ValueError,
                exc_msg=(
                    f"Indicated severity ({bad_severity}) of custom check "
                    "(bad_severity_function) is not a valid severity level! Please choose one of "
                    "Severity.HIGH, Severity.LOW, or do not specify any severity."
                ),
            ):

                @register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=None)
                def bad_severity_function(time_series: TimeSeries):
                    return dict(severity=bad_severity)

                bad_severity_function(time_series=self.default_time_series)

    def test_register_severity_error_enum_type(self):
        class SomeRandomEnum(Enum):
            random_name = -1

        bad_severity = SomeRandomEnum.random_name

        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated severity ({bad_severity}) of custom check "
                "(bad_severity_function) is not a valid severity level! Please choose one of "
                "Severity.HIGH, Severity.LOW, or do not specify any severity."
            ),
        ):

            @register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=None)
            def bad_severity_function(time_series: TimeSeries):
                return dict(severity=bad_severity)

            bad_severity_function(time_series=self.default_time_series)

    def test_register_all_severity_levels(self):
        importance = Importance.BEST_PRACTICE_SUGGESTION
        for severity in Severity:

            @register_check(importance=importance, neurodata_type=TimeSeries)
            def good_check_function(time_series: TimeSeries):
                return dict(severity=severity)

            self.assertEqual(
                first=good_check_function(time_series=self.default_time_series),
                second=dict(
                    severity=severity.name,
                    importance=importance.name,
                    check_function_name="good_check_function",
                    object_type="TimeSeries",
                    object_name="temp",
                    location="/",
                ),
            )

    def test_register_none_severity(self):
        importance = Importance.BEST_PRACTICE_SUGGESTION

        @register_check(importance=importance, neurodata_type=TimeSeries)
        def good_check_function(time_series: TimeSeries):
            return dict(severity=None)

        self.assertEqual(
            first=good_check_function(time_series=self.default_time_series),
            second=dict(
                severity=Severity.NO_SEVERITY.name,
                importance=importance.name,
                check_function_name="good_check_function",
                object_type="TimeSeries",
                object_name="temp",
                location="/",
            ),
        )

    def test_register_missing_severity(self):
        importance = Importance.BEST_PRACTICE_SUGGESTION

        @register_check(importance=importance, neurodata_type=TimeSeries)
        def good_check_function(time_series: TimeSeries):
            return dict()

        self.assertEqual(
            first=good_check_function(time_series=self.default_time_series),
            second=dict(
                severity=Severity.NO_SEVERITY.name,
                importance=importance.name,
                check_function_name="good_check_function",
                object_type="TimeSeries",
                object_name="temp",
                location="/",
            ),
        )

    def test_register_available_checks_all_importance_levels_same_neurodata_type(self):
        from nwbinspector import available_checks

        neurodata_type = DynamicTable
        for importance in Importance:

            @register_check(importance=importance, neurodata_type=neurodata_type)
            def good_check_function():
                pass

            self.assertFunctionInChecks(
                check_function=good_check_function, available_checks=available_checks[importance][neurodata_type]
            )

    def test_register_available_checks_same_importance_level_different_neurodata_types(self):
        from nwbinspector import available_checks

        importance = Importance.BEST_PRACTICE_VIOLATION
        neurodata_type_1 = DynamicTable
        neurodata_type_2 = TimeSeries

        @register_check(importance=importance, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

            self.assertFunctionInChecks(
                check_function=good_check_function_1,
                available_checks=available_checks[importance][neurodata_type_1],
            )

        @register_check(importance=importance, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_2,
            available_checks=available_checks[importance][neurodata_type_2],
        )

    def test_register_available_checks_different_importance_levels_different_neurodata_types(self):
        from nwbinspector import available_checks

        importance_1 = Importance.BEST_PRACTICE_SUGGESTION
        importance_2 = Importance.BEST_PRACTICE_VIOLATION
        neurodata_type_1 = DynamicTable
        neurodata_type_2 = TimeSeries

        @register_check(importance=importance_1, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_1,
            available_checks=available_checks[importance_1][neurodata_type_1],
        )

        @register_check(importance=importance_2, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        self.assertFunctionInChecks(
            check_function=good_check_function_2,
            available_checks=available_checks[importance_2][neurodata_type_2],
        )
