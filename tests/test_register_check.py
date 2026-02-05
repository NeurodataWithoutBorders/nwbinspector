from datetime import datetime
from enum import Enum

import pynwb
from hdmf.common import DynamicTable
from hdmf.testing import TestCase
from packaging import version
from pynwb import TimeSeries

from nwbinspector import Importance, InspectorMessage, Severity, register_check
from nwbinspector._nwb_inspection import run_checks


class TestRegisterClass(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.default_time_series = TimeSeries(name="temp", data=[], unit="", rate=1.0)

    def assertFunctionInChecks(self, check_function, available_checks):
        function_names = [x.__name__ for x in available_checks]
        self.assertIn(member=check_function.__name__, container=function_names)

    def test_register_importance_error_non_enum_type(self):
        bad_importance = "test_bad_importance"

        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated importance ({bad_importance}) of custom check (bad_importance_function) is not a valid "
                "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                "or Importance.BEST_PRACTICE_SUGGESTION."
            ),
        ):

            @register_check(importance=bad_importance, neurodata_type=None)
            def bad_importance_function():
                pass

    def test_register_importance_error_enum_type(self):
        class SomeRandomEnum(Enum):
            random_name = -1

        bad_importance = SomeRandomEnum.random_name

        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg=(
                f"Indicated importance ({bad_importance}) of custom check (bad_importance_function) is not a valid "
                "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                "or Importance.BEST_PRACTICE_SUGGESTION."
            ),
        ):

            @register_check(importance=bad_importance, neurodata_type=None)
            def bad_importance_function():
                pass

    def test_register_importance_error_both_forbidden_check_levels(self):
        for forbidden_importance in [Importance.ERROR, Importance.PYNWB_VALIDATION]:
            with self.assertRaisesWith(
                exc_type=ValueError,
                exc_msg=(
                    f"Indicated importance ({forbidden_importance}) of custom check (forbidden_importance_function) is "
                    "not a valid importance level! Please choose one of Importance.CRITICAL, "
                    "Importance.BEST_PRACTICE_VIOLATION, or Importance.BEST_PRACTICE_SUGGESTION."
                ),
            ):

                @register_check(importance=forbidden_importance, neurodata_type=None)
                def forbidden_importance_function():
                    pass

    def test_register_severity_error(self):
        bad_severity = "test_bad_severity"

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
                return InspectorMessage(severity=bad_severity, message="")

            bad_severity_function(time_series=self.default_time_series)

    def test_register_all_severity_levels(self):
        importance = Importance.BEST_PRACTICE_SUGGESTION
        for severity in Severity:

            @register_check(importance=importance, neurodata_type=TimeSeries)
            def good_check_function(time_series: TimeSeries):
                return InspectorMessage(severity=severity, message="")

            self.assertEqual(
                first=good_check_function(time_series=self.default_time_series),
                second=InspectorMessage(
                    severity=severity,
                    message="",
                    importance=importance,
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
            return InspectorMessage(message="")

        self.assertEqual(
            first=good_check_function(time_series=self.default_time_series),
            second=InspectorMessage(
                message="",
                importance=importance,
                severity=Severity.LOW,
                check_function_name="good_check_function",
                object_type="TimeSeries",
                object_name="temp",
                location="/",
            ),
        )

    def test_register_available_checks_all_importance_levels_same_neurodata_type(self):
        from nwbinspector import available_checks

        neurodata_type = DynamicTable
        for importance in [
            Importance.CRITICAL,
            Importance.BEST_PRACTICE_VIOLATION,
            Importance.BEST_PRACTICE_SUGGESTION,
        ]:

            @register_check(importance=importance, neurodata_type=neurodata_type)
            def good_check_function():
                pass

            assert good_check_function in available_checks

    def test_register_available_checks_same_importance_level_different_neurodata_types(self):
        from nwbinspector import available_checks

        importance = Importance.BEST_PRACTICE_VIOLATION
        neurodata_type_1 = DynamicTable
        neurodata_type_2 = TimeSeries

        @register_check(importance=importance, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        assert good_check_function_1 in available_checks

        @register_check(importance=importance, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        assert good_check_function_2 in available_checks

    def test_register_available_checks_different_importance_levels_different_neurodata_types(self):
        from nwbinspector import available_checks

        importance_1 = Importance.BEST_PRACTICE_SUGGESTION
        importance_2 = Importance.BEST_PRACTICE_VIOLATION
        neurodata_type_1 = DynamicTable
        neurodata_type_2 = TimeSeries

        @register_check(importance=importance_1, neurodata_type=neurodata_type_1)
        def good_check_function_1():
            pass

        assert good_check_function_1 in available_checks

        @register_check(importance=importance_2, neurodata_type=neurodata_type_2)
        def good_check_function_2():
            pass

        assert good_check_function_2 in available_checks

    def test_register_schema_version_lt(self):
        """Test that nwb_schema_version_lt is stored on the check function."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=TimeSeries,
            nwb_schema_version_lt="2.5.0",
        )
        def check_with_version_lt(time_series: TimeSeries):
            return InspectorMessage(message="test")

        self.assertEqual(check_with_version_lt.nwb_schema_version_lt, "2.5.0")
        self.assertIsNone(check_with_version_lt.nwb_schema_version_gt)

    def test_register_schema_version_gt(self):
        """Test that nwb_schema_version_gt is stored on the check function."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=TimeSeries,
            nwb_schema_version_gt="2.3.0",
        )
        def check_with_version_gt(time_series: TimeSeries):
            return InspectorMessage(message="test")

        self.assertIsNone(check_with_version_gt.nwb_schema_version_lt)
        self.assertEqual(check_with_version_gt.nwb_schema_version_gt, "2.3.0")

    def test_register_schema_version_both(self):
        """Test that both version constraints can be set."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=TimeSeries,
            nwb_schema_version_lt="2.5.0",
            nwb_schema_version_gt="2.3.0",
        )
        def check_with_both_versions(time_series: TimeSeries):
            return InspectorMessage(message="test")

        self.assertEqual(check_with_both_versions.nwb_schema_version_lt, "2.5.0")
        self.assertEqual(check_with_both_versions.nwb_schema_version_gt, "2.3.0")


class TestSchemaVersionFiltering(TestCase):
    """Test that run_checks properly filters checks based on schema version."""

    @classmethod
    def setUpClass(cls):
        cls.nwbfile = pynwb.NWBFile(
            session_description="test",
            identifier="test",
            session_start_time=datetime.now(),
        )

    def test_run_checks_skips_check_when_version_lt_not_met(self):
        """Test that a check with nwb_schema_version_lt is skipped when file version is >= threshold."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_lt="2.5.0",
        )
        def check_for_old_files_only(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should be skipped for newer files")

        # File version 2.6.0 is >= 2.5.0, so check should be skipped
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_old_files_only],
                nwb_schema_version=version.parse("2.6.0"),
            )
        )
        self.assertEqual(len(results), 0)

    def test_run_checks_runs_check_when_version_lt_is_met(self):
        """Test that a check with nwb_schema_version_lt is run when file version is < threshold."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_lt="2.5.0",
        )
        def check_for_old_files_lt(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should run for older files")

        # File version 2.4.0 is < 2.5.0, so check should run
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_old_files_lt],
                nwb_schema_version=version.parse("2.4.0"),
            )
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].message, "This should run for older files")

    def test_run_checks_skips_check_when_version_gt_not_met(self):
        """Test that a check with nwb_schema_version_gt is skipped when file version is <= threshold."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_gt="2.5.0",
        )
        def check_for_new_files_only(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should be skipped for older files")

        # File version 2.4.0 is <= 2.5.0, so check should be skipped
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_new_files_only],
                nwb_schema_version=version.parse("2.4.0"),
            )
        )
        self.assertEqual(len(results), 0)

    def test_run_checks_runs_check_when_version_gt_is_met(self):
        """Test that a check with nwb_schema_version_gt is run when file version is > threshold."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_gt="2.5.0",
        )
        def check_for_new_files_gt(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should run for newer files")

        # File version 2.6.0 is > 2.5.0, so check should run
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_new_files_gt],
                nwb_schema_version=version.parse("2.6.0"),
            )
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].message, "This should run for newer files")

    def test_run_checks_with_both_version_constraints(self):
        """Test that a check with both version constraints works correctly."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_lt="2.7.0",
            nwb_schema_version_gt="2.3.0",
        )
        def check_for_version_range(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should run for versions in range")

        # File version 2.5.0 is > 2.3.0 and < 2.7.0, so check should run
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_version_range],
                nwb_schema_version=version.parse("2.5.0"),
            )
        )
        self.assertEqual(len(results), 1)

        # File version 2.2.0 is <= 2.3.0, so check should be skipped
        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_lt="2.7.0",
            nwb_schema_version_gt="2.3.0",
        )
        def check_for_version_range_2(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should be skipped")

        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_for_version_range_2],
                nwb_schema_version=version.parse("2.2.0"),
            )
        )
        self.assertEqual(len(results), 0)

    def test_run_checks_without_version_constraints_always_runs(self):
        """Test that a check without version constraints always runs regardless of file version."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
        )
        def check_without_version_constraints(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="This should always run")

        # Should run with any version
        for ver in ["2.0.0", "2.5.0", "3.0.0"]:
            results = list(
                run_checks(
                    nwbfile=self.nwbfile,
                    checks=[check_without_version_constraints],
                    nwb_schema_version=version.parse(ver),
                )
            )
            self.assertEqual(len(results), 1)

    def test_run_checks_without_schema_version_runs_all_checks(self):
        """Test that when no schema version is provided, all checks run regardless of constraints."""

        @register_check(
            importance=Importance.BEST_PRACTICE_SUGGESTION,
            neurodata_type=None,
            nwb_schema_version_lt="2.0.0",  # Very restrictive constraint
        )
        def check_with_restrictive_lt(nwbfile: pynwb.NWBFile):
            return InspectorMessage(message="Should run when no version provided")

        # When nwb_schema_version is None, checks should run regardless of constraints
        results = list(
            run_checks(
                nwbfile=self.nwbfile,
                checks=[check_with_restrictive_lt],
                nwb_schema_version=None,
            )
        )
        self.assertEqual(len(results), 1)
