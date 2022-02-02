"""Authors: Cody Baker and Ben Dichter."""
from collections import defaultdict, OrderedDict
from functools import wraps
from enum import Enum
from dataclasses import dataclass

import h5py


class Importance(Enum):
    """A definition of the valid importance levels for a given check function."""

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
    NO_SEVERITY = 0


global available_checks
available_checks = OrderedDict({importance: defaultdict(list) for importance in Importance})


@dataclass
class InspectorMessage:
    """The primary result returned by every check."""

    message: str
    severity: Severity = None
    importance: Importance = Importance.BEST_PRACTICE_SUGGESTION
    check_function_name: str = ""
    object_type: str = ""
    object_name: str = ""
    location: str = ""


def register_check(importance, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def register_check_and_auto_parse(check_function):
        if importance not in Importance:
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                "importance level! Please choose one of Importance.CRITICAL, Importance.BEST_PRACTICE_VIOLATION, "
                "or Importance.BEST_PRACTICE_SUGGESTION."
            )
        check_function.importance = importance
        check_function.neurodata_type = neurodata_type

        @wraps(check_function)
        def auto_parse_some_output(*args, **kwargs):
            if args:
                obj = args[0]
            else:
                obj = kwargs[list(kwargs)[0]]

            auto_parsed_result = check_function(*args, **kwargs)
            if auto_parsed_result is not None:
                if auto_parsed_result.severity is None:  # For perfect consistency with not specifying
                    auto_parsed_result.severity = Severity.NO_SEVERITY
                if auto_parsed_result.severity not in Severity:
                    raise ValueError(
                        f"Indicated severity ({auto_parsed_result.severity}) of custom check "
                        f"({check_function.__name__}) is not a valid severity level! Please choose one of "
                        "Severity.HIGH, Severity.LOW, or do not specify any severity."
                    )

                auto_parsed_result.importance = check_function.importance
                auto_parsed_result.check_function_name = check_function.__name__
                auto_parsed_result.object_type = type(obj).__name__
                auto_parsed_result.object_name = obj.name
                auto_parsed_result.location = parse_location(nwbfile_object=obj)
            return auto_parsed_result

        available_checks[check_function.importance][check_function.neurodata_type].append(auto_parse_some_output)

        return auto_parse_some_output

    return register_check_and_auto_parse


def parse_location(nwbfile_object):
    """Infer the human-readable path of the object within an NWBFile by tracing its parents."""
    if nwbfile_object.parent is None:
        return "/"

    # Best solution: object is or has a HDF5 Dataset
    if isinstance(nwbfile_object, h5py.Dataset):
        return "/".join(nwbfile_object.parent.name.split("/")[:-1]) + "/"
    else:
        for field in nwbfile_object.fields.values():
            if isinstance(field, h5py.Dataset):
                return "/".join(field.parent.name.split("/")[:-1]) + "/"

    try:
        # General case for nested modules not containing Datasets
        level = nwbfile_object
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
