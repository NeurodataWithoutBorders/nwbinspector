from ._version import __version__
from ._registration import available_checks, register_check
from ._types import Importance, Severity, InspectorMessage
from ._configuration import load_config, InspectorOutputJSONEncoder
from ._inspection import (
    inspect_all,
    inspect_nwbfile,
    inspect_nwbfile_object,
    run_checks,
)
from ._inspection import inspect_nwb  # TODO: remove after 7/1/2023
from ._formatting import format_messages, print_to_console, save_report, MessageFormatter, FormatterOptions
from ._organization import organize_messages
from .checks.ecephys import *
from .checks.general import *
from .checks.image_series import *
from .checks.images import *
from .checks.nwb_containers import *
from .checks.nwbfile_metadata import *
from .checks.ogen import *
from .checks.ophys import *
from .checks.tables import *
from .checks.time_series import *
from .checks.icephys import *

default_check_registry = {check.__name__: check for check in available_checks}

__all__ = [
    "available_checks",
    "default_check_registry",
    "register_check",
    "Importance",
    "Severity",
    "InspectorMessage",
    "load_config",
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
