"""Commonly reused logic for evaluating conditions; must not have external dependencies."""
import numpy as np
from typing import TypeVar, Optional, List
from pathlib import Path

PathType = TypeVar("PathType", str, Path)  # For types that can be either files or folders
FilePathType = TypeVar("FilePathType", str, Path)
OptionalListOfStrings = Optional[List[str]]


def format_byte_size(byte_size: int, units: str = "SI"):
    """
    Format a number representing a total number of bytes into a conveneient unit.

    Parameters
    ----------
    byte_size : int
        Total number of bytes to format.
    units : str, optional
        Convention for orders of magnitude to apply.
        May be either SI (orders of 1000) or binary (in memory, orders of 1024).
        The default is SI.
    """
    num = byte_size
    prefixes = ["", "K", "M", "G", "T", "P", "E", "Z"]
    if units == "SI":
        order = 1000.0
        suffix = "B"
    elif units == "binary":
        order = 1024.0
        suffix = "iB"
    else:
        raise ValueError("'units' argument must be either 'SI' (for orders of 1000) or 'binary' (for orders of 1024).")
    for prefix in prefixes:
        if abs(num) < order:
            return f"{num:3.2f}{prefix}{suffix}"
        num /= order
    return f"{num:.2f}Y{suffix}"


def check_regular_series(series: np.ndarray, tolerance_decimals: int = 9):
    """General purpose function for checking if the difference between all consecutive points in a series are equal."""
    uniq_diff_ts = np.unique(np.diff(series).round(decimals=tolerance_decimals))
    return len(uniq_diff_ts) == 1


def is_ascending_series(series: np.ndarray, nelems=None):
    return np.all(np.diff(series[:nelems]) > 0)
