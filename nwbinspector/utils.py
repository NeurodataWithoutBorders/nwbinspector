"""Commonly reused logic for evaluating conditions; must not have external dependencies."""
import numpy as np
from typing import TypeVar, Optional, List
from pathlib import Path

PathType = TypeVar("PathType", str, Path)  # For types that can be either files or folders
FilePathType = TypeVar("FilePathType", str, Path)
OptionalListOfStrings = Optional[List[str]]


def check_regular_series(series: np.ndarray, tolerance_decimals: int = 9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1


def is_ascending_series(series: np.ndarray, nelems=None):
    return np.all(np.diff(series[:nelems]) > 0)
