"""Commonly reused logic for evaluating conditions; must not have external dependencies."""
import os
import re
import json
import numpy as np
from typing import TypeVar, Optional, List
from pathlib import Path
from importlib import import_module
from packaging import version

PathType = TypeVar("PathType", str, Path)  # For types that can be either files or folders
FilePathType = TypeVar("FilePathType", str, Path)
OptionalListOfStrings = Optional[List[str]]

dict_regex = r"({.+:.+})"


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
    """General purpose function for determining if a series is monotonic increasing."""
    return np.all(np.diff(series[:nelems]) > 0)


def is_dict_in_string(string: str):
    """
    Determine if the string value contains an encoded Python dictionary.

    Can also be the direct results of string casting a dictionary, *e.g.*, ``str(dict(a=1))``.
    """
    return any(re.findall(pattern=dict_regex, string=string))


def is_string_json_loadable(string: str):
    """
    Determine if the serialized dictionary is a JSON object.

    Rather than constructing a complicated regex pattern, a simple try/except of the json.load should suffice.
    """
    try:
        json.loads(string)
        return True
    except json.JSONDecodeError:
        return False


def is_module_installed(module_name: str):
    """
    Check if the given module is installed on the system.

    Used for lazy imports.
    """
    try:
        import_module(name=module_name)
        return True
    except ModuleNotFoundError:
        return False


def get_package_version(name: str) -> version.Version:
    """
    Retrieve the version of a package regardless of if it has a __version__ attribute set.

    Parameters
    ----------
    name : str
        Name of package.

    Returns
    -------
    version : Version
        The package version as an object from packaging.version.Version, which allows comparison to other versions.
    """
    try:
        from importlib.metadata import version as importlib_version

        package_version = importlib_version(name)
    except ModuleNotFoundError:  # Remove the except clause when minimal supported version becomes 3.8
        from pkg_resources import get_distribution

        package_version = get_distribution(name).version
    return version.parse(package_version)


def calculate_number_of_cpus(requested_cpu: int = 1) -> int:
    """
    Calculate the number CPUs to use with respect to negative slicing and check against maximal available resources.

    Parameters
    ----------
    requested_cpu : int, optional
        The desired number of CPUs to use.
        
        The default is 1.
    """
    total_cpu = os.cpu_count()
    assert requested_cpu <= total_cpu, "Requested more CPUs ({requested_cpu}) than are available ({total_cpu})!"
    assert requested_cpu >= -(total_cpu - 1)
