"""Authors: Cody Baker and Ben Dichter."""
from collections import defaultdict, OrderedDict
from functools import wraps

import h5py

global available_checks
CRITICAL_IMPORTANCE = 2
BEST_PRACTICE_VIOLATION = 1
BEST_PRACTICE_SUGGESTION = 0

importance_levels = OrderedDict(
    CRITICAL_IMPORTANCE=CRITICAL_IMPORTANCE,
    BEST_PRACTICE_VIOLATION=BEST_PRACTICE_VIOLATION,
    BEST_PRACTICE_SUGGESTION=BEST_PRACTICE_SUGGESTION,
)
levels_to_importance = {v: k for k, v in importance_levels.items()}
available_checks = OrderedDict({importance_level: defaultdict(list) for importance_level in importance_levels})

# For strictly internal use only
HIGH_SEVERITY = 5
LOW_SEVERITY = 4
severity_levels = OrderedDict({"HIGH_SEVERITY": HIGH_SEVERITY, "LOW_SEVERITY": LOW_SEVERITY, None: 3})
levels_to_severity = {v: k for k, v in severity_levels.items()}


def register_check(importance, neurodata_type):
    """Wrap a check function to add it to the list of default checks for that severity and neurodata type."""

    def register_check_and_auto_parse(check_function):
        if importance not in importance_levels.values():
            raise ValueError(
                f"Indicated importance ({importance}) of custom check ({check_function.__name__}) is not a valid "
                "importance level! Please choose from [CRITICAL_IMPORTANCE, BEST_PRACTICE_VIOLATION, "
                "BEST_PRACTICE_SUGGESTION]."
            )
        check_function.importance = levels_to_importance[importance]
        check_function.neurodata_type = neurodata_type

        @wraps(check_function)
        def auto_parse_some_output(*args, **kwargs):
            if args:
                obj = args[0]
            else:
                obj = kwargs[list(kwargs)[0]]
            auto_parsed_result = check_function(*args, **kwargs)
            if auto_parsed_result is not None:
                auto_parsed_result.update(
                    importance=check_function.importance,
                    severity=levels_to_severity[auto_parsed_result.get("severity", severity_levels[None])],
                    check_function_name=check_function.__name__,
                    object_type=type(obj).__name__,
                    object_name=obj.name,
                    location=parse_location(nwbfile_object=obj),
                )
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
        return "unknown"
