"""Primary decorator used on a check function to add it to the registry and automatically parse its output."""
from collections import Iterable
from functools import wraps
from enum import Enum
from dataclasses import dataclass
from typing import Optional

import h5py


class Importance(Enum):
    """A definition of the valid importance levels for a given check function."""

    ERROR = 4
    PYNWB_VALIDATION = 3
    CRITICAL = 2
    BEST_PRACTICE_VIOLATION = 1
    BEST_PRACTICE_SUGGESTION = 0


class Severity(Enum):
    """
    A definition of the valid severity levels for the output from a given check function.

    Strictly for internal development that improves report organization; users should never directly see these values.
    """

    HIGH = 2
    LOW = 1


available_checks = list()


@dataclass
class InspectorMessage:
    """
    The primary output to be returned by every check function.

    Parameters
    ----------
    message : str
        A message that informs the user of the violation.
    severity : Severity, optional
        If a check of non-CRITICAL importance has some basis of comparison, such as magitude of affected data, then
        the developer of the check may set the severity as Severity.HIGH or Severity.LOW by calling
        `from nwbinspector.register_checks import Severity`. A good example is comparing if h5py.Dataset compression
        has been enabled on smaller vs. larger objects (see nwbinspect/checks/nwb_containers.py for details).

        The user will never directly see this severity, but it will prioritize the order in which check results are
        presented by the NWBInspector.

    importance : Importance
        The Importance level specified by the decorator of the check function.
    check_function_name : str
        The name of the check function the decorator was applied to.
    object_type : str
        The specific class of the instantiated object being inspected.
    object_name : str
        The name of the instantiated object being inspected.
    location : str
        The location relative to the root of the NWBFile where the inspected object may be found.
    file_path : str
        The path of the NWBFile this message pertains to
        Relative to the path called from inspect_nwb, inspect_all, or the path specified at the command line.
    """

    message: str
    importance: Importance = Importance.BEST_PRACTICE_SUGGESTION
    severity: Severity = Severity.LOW
    check_function_name: str = ""
    object_type: str = ""
    object_name: str = ""
    location: str = ""
    file_path: str = ""


# TODO: neurodata_type could have annotation hdmf.utils.ExtenderMeta, which seems to apply to all currently checked
# objects. We can wait and see how well that holds up before adding it in officially.
def register_check(importance: Importance, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def register_check_and_auto_parse(check_function):
        if importance not in [
            Importance.CRITICAL,
            Importance.BEST_PRACTICE_VIOLATION,
            Importance.BEST_PRACTICE_SUGGESTION,
        ]:
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                "or Importance.BEST_PRACTICE_SUGGESTION."
            )
        check_function.importance = importance
        check_function.neurodata_type = neurodata_type

        @wraps(check_function)
        def auto_parse_some_output(*args, **kwargs) -> InspectorMessage:

            if args:
                obj = args[0]
            else:
                obj = kwargs[list(kwargs)[0]]
            output = check_function(*args, **kwargs)
            if isinstance(output, Iterable):
                auto_parsed_result = list()
                for result in output:
                    auto_parsed_result.append(auto_parse(check_function=check_function, obj=obj, result=result))
                if not any(auto_parsed_result):
                    auto_parsed_result = None
            else:
                auto_parsed_result = auto_parse(check_function=check_function, obj=obj, result=output)
            return auto_parsed_result

        available_checks.append(auto_parse_some_output)

        return auto_parse_some_output

    return register_check_and_auto_parse


def auto_parse(check_function, obj, result: Optional[InspectorMessage] = None):
    """Automatically fill values in the InspectorMessage from the check function."""
    if result is not None:
        auto_parsed_result = result
        if not isinstance(auto_parsed_result.severity, Severity):
            raise ValueError(
                f"Indicated severity ({auto_parsed_result.severity}) of custom check "
                f"({check_function.__name__}) is not a valid severity level! Please choose one of "
                "Severity.HIGH, Severity.LOW, or do not specify any severity."
            )
        auto_parsed_result.importance = check_function.importance
        auto_parsed_result.check_function_name = check_function.__name__
        auto_parsed_result.object_type = type(obj).__name__
        auto_parsed_result.object_name = obj.name
        auto_parsed_result.location = parse_location(neurodata_object=obj)
        return auto_parsed_result


def parse_location(neurodata_object) -> str:
    """Infer the human-readable path of the object within an NWBFile by tracing its parents."""
    if neurodata_object.parent is None:
        return "/"
    # Best solution: object is or has a HDF5 Dataset
    if isinstance(neurodata_object, h5py.Dataset):
        return "/".join(neurodata_object.parent.name.split("/")[:-1]) + "/"
    else:
        for field in neurodata_object.fields.values():
            if isinstance(field, h5py.Dataset):
                return "/".join(field.parent.name.split("/")[:-1]) + "/"
    try:
        # General case for nested modules not containing Datasets
        level = neurodata_object
        level_names = []
        while level.parent.name != "root":
            level_names.append(level.parent.name)
            level = level.parent
        # Determine which field of the NWBFile contains the previous recent level
        invalid_field_names = ["timestamps_reference_time", "session_start_time"]
        possible_fields = level.parent.fields
        for field_name in invalid_field_names:
            if field_name in possible_fields:
                possible_fields.pop(field_name)
        for field_name, field in possible_fields.items():
            if level.name in field:
                level_names.append(field_name)
        return "/" + "/".join(level_names[::-1]) + "/"
    except Exception:
        return ""
