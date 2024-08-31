"""Primary functions for inspecting NWBFiles."""

import json
from pathlib import Path
from types import FunctionType
from typing import List, Optional

import jsonschema
import yaml

from nwbinspector.utils._utils import (
    PathType,
)

from . import available_checks
from ._registration import Importance

INTERNAL_CONFIGS = dict(dandi=Path(__file__).parent / "internal_configs" / "dandi.inspector_config.yaml")


def validate_config(config: dict):
    """Validate an instance of configuration against the official schema."""
    with open(file=Path(__file__).parent / "config.schema.json", mode="r") as fp:
        schema = json.load(fp=fp)
    jsonschema.validate(instance=config, schema=schema)


def _copy_function(function):
    """Copy the core parts of a given function, excluding wrappers, then return a new function."""
    copied_function = FunctionType(
        function.__code__, function.__globals__, function.__name__, function.__defaults__, function.__closure__
    )

    # in case f was given attrs (note this dict is a shallow copy)
    copied_function.__dict__.update(function.__dict__)
    return copied_function


def copy_check(check):
    """
    Copy a check function so that internal attributes can be adjusted without changing the original function.

    Required to ensure our configuration of functions in the registry does not effect the registry itself.

    Also copies the wrapper for auto-parsing results,
    see https://github.com/NeurodataWithoutBorders/nwbinspector/pull/218 for explanation.
    """
    copied_check = _copy_function(function=check)
    copied_check.__wrapped__ = _copy_function(function=check.__wrapped__)
    return copied_check


def load_config(filepath_or_keyword: PathType) -> dict:
    """
    Load a config dictionary either via keyword search of the internal configs, or an explicit filepath.

    Currently supported keywords are:
        - 'dandi'
            For all DANDI archive related practices, including validation and upload.
    """
    file = INTERNAL_CONFIGS.get(filepath_or_keyword, filepath_or_keyword)
    with open(file=file, mode="r") as stream:
        config = yaml.load(stream=stream, Loader=yaml.Loader)
    return config


def configure_checks(
    checks: list = available_checks,
    config: Optional[dict] = None,
    ignore: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    importance_threshold: Importance = Importance.BEST_PRACTICE_SUGGESTION,
) -> list:
    """
    Filter a list of check functions (the entire base registry by default) according to the configuration.

    Parameters
    ----------
    config : dict
        Dictionary valid against our JSON configuration schema.
        Can specify a mapping of importance levels and list of check functions whose importance you wish to change.
        Typically loaded via json.load from a valid .json file
    checks : list of check functions
        Defaults to all registered checks.
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
        If loading all registered checks, this can be shorthand for selecting only a handful of them.
    importance_threshold : string, optional
        Ignores all tests with an post-configuration assigned importance below this threshold.
        Importance has three levels:

            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation

        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    """
    if ignore is not None and select is not None:
        raise ValueError("Options 'ignore' and 'select' cannot both be used.")
    if importance_threshold not in Importance:
        raise ValueError(
            f"Indicated importance_threshold ({importance_threshold}) is not a valid importance level! Please choose "
            "from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, BEST_PRACTICE_SUGGESTION]."
        )
    if config is not None:
        validate_config(config=config)
        checks_out = []
        ignore = ignore or []
        for check in checks:
            mapped_check = copy_check(check=check)
            for importance_name, func_names in config.items():
                if check.__name__ in func_names:
                    if importance_name == "SKIP":
                        ignore.append(check.__name__)
                        continue
                    mapped_check.importance = Importance[importance_name]
                    # Output wrappers are apparently parsed at time of wrapping not of time of output return...
                    # Attempting to re-wrap the copied function if the importance level is being adjusted...
                    # From https://github.com/NeurodataWithoutBorders/nwbinspector/issues/302
                    # new_check_wrapper = _copy_function(function=mapped_check.__wrapped__)
                    # new_check_wrapper.importance = Importance[importance_name]
                    # mapped_check.__wrapped__ = new_check_wrapper
            checks_out.append(mapped_check)
    else:
        checks_out = checks
    if select:
        checks_out = [x for x in checks_out if x.__name__ in select]
    elif ignore:
        checks_out = [x for x in checks_out if x.__name__ not in ignore]
    if importance_threshold:
        checks_out = [x for x in checks_out if x.importance.value >= importance_threshold.value]
    return checks_out
