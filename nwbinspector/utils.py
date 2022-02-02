"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from typing import Union
from pathlib import Path

FilePathType = Union[Path, str]


def check_regular_series(series: np.ndarray, tolerance_decimals=9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1
