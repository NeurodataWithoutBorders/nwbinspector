"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
<<<<<<< HEAD
from collections import defaultdict

global available_checks
available_checks = {1: defaultdict(list), 2: defaultdict(list), 3: defaultdict(list)}


def nwbinspector_check(severity: int, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def decorator(check_function):
        if severity not in [1, 2, 3]:
            raise ValueError(
                f"Indicated severity ({severity}) of custom check ({check_function.__name__}) is not in range of 1-3."
            )
        check_function.severity = severity
        check_function.neurodata_type = neurodata_type

        available_checks[severity][neurodata_type].append(check_function)
        return check_function

    return decorator
=======
from collections import defaultdict, OrderedDict

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

    def add_check_to_global_dict(check_function):
        if importance not in importance_levels:
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                f"importance level! Please choose from {importance_levels}."
            )
        check_function.importance = importance
        check_function.neurodata_type = neurodata_type

        available_checks[importance][neurodata_type].append(check_function)
        return check_function

    return add_check_to_global_dict


# def parse_output(check_function):
#     """Wrap a check function to automatically add NWBFile level details to the output."""

#     def add_object_info(*args, **kwargs):
#         if "neurodata_type" not in kwargs:
#             raise ValueError("Expected keyword 'neurodata_type' in check function.")
#         neurodata_type = kwargs.pop("neurodata_type")
#         check_result = check_function(*args, neurodata_type=neurodata_type, **kwargs)
#         check_result.update(
#             check_function_name=check_function.__name__,
#             object_type=type(obj).__name__,
#             object_name=obj.name
#         )
#         return check_result

#     return add_object_info
>>>>>>> squash_refactor_changelog


def check_regular_series(series: np.ndarray, tolerance_decimals=9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1
