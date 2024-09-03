"""Primary decorator used on a check function to add it to the registry and automatically parse its output."""

from functools import wraps
from typing import Optional

import h5py
from pynwb import NWBFile
from pynwb.ecephys import Device, ElectrodeGroup
from pynwb.file import Subject

from ._types import Importance, InspectorMessage, Severity

available_checks = list()


# TODO: neurodata_type could have annotation hdmf.utils.ExtenderMeta, which seems to apply to all currently checked
# objects. We can wait and see how well that holds up before adding it in officially.
def register_check(importance: Importance, neurodata_type):
    """
    Wrap a check function with this decorator to add it to the check registry and automatically parse some output.

    Parameters
    ----------
    importance : Importance
        Importance has three levels:
            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation
    neurodata_type
        The most generic HDMF/PyNWB class the check function applies to.
        Should generally match the type annotation of the check.
        If this check is intended to apply to any general NWBFile object, set neurodata_type to None.
    """

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
            auto_parsed_result = None
            if isinstance(output, InspectorMessage):
                auto_parsed_result = _auto_parse(check_function=check_function, obj=obj, result=output)
            elif output is not None:
                auto_parsed_result = list()
                for result in output:
                    auto_parsed_result.append(_auto_parse(check_function=check_function, obj=obj, result=result))
                if not any(auto_parsed_result):
                    auto_parsed_result = None
            return auto_parsed_result

        available_checks.append(auto_parse_some_output)

        return auto_parse_some_output

    return register_check_and_auto_parse


def _auto_parse(check_function, obj, result: Optional[InspectorMessage] = None):
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
        auto_parsed_result.location = _parse_location(neurodata_object=obj)
        return auto_parsed_result


def _parse_location(neurodata_object) -> Optional[str]:
    """Grab the object location from a h5py.Dataset or a container content that is an h5py.Dataset object."""
    known_locations = {
        NWBFile: "/",
        Subject: "/general/subject",
        Device: f"/general/devices/{neurodata_object.name}",
        ElectrodeGroup: f"/general/extracellular_ephys/{neurodata_object.name}",
        # TODO: add ophys equivalents
    }

    for key, val in known_locations.items():
        if isinstance(neurodata_object, key):
            return val
    """Infer the human-readable path of the object within an NWBFile by tracing its parents."""
    if neurodata_object.parent is None:
        return "/"
    # Best solution: object is or has a HDF5 Dataset
    if isinstance(neurodata_object, h5py.Dataset):
        return neurodata_object.name
    else:
        for field in neurodata_object.fields.values():
            if isinstance(field, h5py.Dataset):
                return field.parent.name
