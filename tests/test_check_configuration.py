from jsonschema import ValidationError
from unittest import TestCase

from nwbinspector import (
    Importance,
    check_small_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
    available_checks,
)
from nwbinspector.nwbinspector import validate_config, configure_checks, copy_function


class TestCheckConfiguration(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checks = [
            check_small_dataset_compression,
            check_regular_timestamps,
            check_data_orientation,
            check_timestamps_match_first_dimension,
        ]

    def test_safe_check_copy(self):
        initial_importance = available_checks[0].importance
        changed_check = copy_function(function=available_checks[0])
        if initial_importance is Importance.CRITICAL:
            changed_importance = Importance.BEST_PRACTICE_SUGGESTION
        else:
            changed_importance = Importance.CRITICAL
        changed_check.importance = changed_importance
        assert available_checks[0].importance is initial_importance
        assert changed_check.importance is changed_importance

    def test_configure_checks_change_importance(self):
        config = dict(
            CRITICAL=["check_small_dataset_compression"],
            BEST_PRACTICE_SUGGESTION=["check_regular_timestamps"],
        )
        checks_out = configure_checks(checks=self.checks, config=config)
        assert (
            checks_out[0].__name__ == "check_small_dataset_compression"
            and checks_out[0].importance is Importance.CRITICAL
        )
        assert (
            checks_out[1].__name__ == "check_regular_timestamps"
            and checks_out[1].importance is Importance.BEST_PRACTICE_SUGGESTION
        )

    def test_configure_checks_no_change(self):
        config = dict(CRITICAL=["check_data_orientation"])
        validate_config(config=config)
        checks_out = configure_checks(checks=self.checks, config=config)
        assert checks_out[2].__name__ == "check_data_orientation", checks_out[2].importance is Importance.CRITICAL

    def test_configure_checks_skip(self):
        config = dict(SKIP=["check_timestamps_match_first_dimension"])
        validate_config(config=config)
        checks_out = configure_checks(checks=self.checks, config=config)
        print([checks_out, self.checks[:3]])
        self.assertListEqual(list1=checks_out, list2=self.checks[:3])

    def test_bad_schema(self):
        config = dict(WRONG="test")
        with self.assertRaises(expected_exception=ValidationError):
            validate_config(config=config)