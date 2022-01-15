"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
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
        check_function.name = check_function.__name__
        check_function.severity = severity
        check_function.neurodata_type = neurodata_type

        available_checks[severity][neurodata_type].append(check_function)
        return check_function

    return decorator


def check_regular_series(series: np.ndarray, tolerance_decimals=9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1
