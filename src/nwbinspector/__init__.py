from ._version import __version__
from ._registration import available_checks, register_check
from ._types import Importance, Severity, InspectorMessage
from ._configuration import load_config, validate_config, configure_checks
from ._inspection import (
    inspect_all,
    inspect_nwbfile,
    inspect_nwbfile_object,
    run_checks,
)
from ._inspection import inspect_nwb  # TODO: remove after 7/1/2023
from ._formatting import (
    format_messages,
    print_to_console,
    save_report,
    MessageFormatter,
    FormatterOptions,
    InspectorOutputJSONEncoder,
)
from ._organization import organize_messages
from .checks import *  # These need to be imported to trigger registration with 'available_checks', but are not exposed

default_check_registry = {check.__name__: check for check in available_checks}

__all__ = [
    "available_checks",
    "default_check_registry",
    "register_check",
    "Importance",
    "Severity",
    "InspectorMessage",
    "validate_config",
    "load_config",
    "configure_checks",
    "InspectorOutputJSONEncoder",
    "inspect_all",
    "inspect_nwbfile",
    "inspect_nwbfile_object",
    "inspect_nwb",  # TODO: remove after 7/1/2023
    "run_checks",
    "format_messages",
    "print_to_console",
    "save_report",
    "MessageFormatter",
    "FormatterOptions",
    "organize_messages",
    "__version__",
]
