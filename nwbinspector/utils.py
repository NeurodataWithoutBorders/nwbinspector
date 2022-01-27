"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from collections import defaultdict, OrderedDict
from functools import wraps

global available_checks, importance_levels
available_checks = OrderedDict(
    {
        importance_level: defaultdict(list)
        for importance_level in ["Best Practice Suggestion", "Best Practice Violation", "DANDI Requirement", "Critical"]
    }
)
importance_levels = list(available_checks.keys())


def register_check(importance: int, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def register_check_and_auto_parse(check_function):
        if importance not in importance_levels:
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                f"importance level! Please choose from {importance_levels}."
            )
        check_function.importance = importance

        available_checks[importance][neurodata_type].append(check_function)

        @wraps(check_function)
        def auto_parse_some_output(*args, **kwargs):
            auto_parsed_result = check_function(*args, **kwargs)
            obj = args[0]
            auto_parsed_result.update(
                importance=check_function.importance,
                check_function_name=check_function.__name__,
                object_type=type(obj).__name__,
                object_name=obj.name,
            )
            return auto_parsed_result

        return auto_parse_some_output

    return register_check_and_auto_parse


def check_regular_series(series: np.ndarray, tolerance_decimals=9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1
