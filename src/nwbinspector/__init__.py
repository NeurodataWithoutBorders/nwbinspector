from .version import __version__
from .register_checks import available_checks, Importance
from .nwbinspector import inspect_all, inspect_nwbfile, inspect_nwbfile_object, run_checks, load_config
from .nwbinspector import inspect_nwb  # TODO: remove after 7/1/2023
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
