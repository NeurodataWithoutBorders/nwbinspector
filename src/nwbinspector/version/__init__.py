import warnings

message = (
    "The 'version' submodule has been deprecated. "
    "Please import the version using `importlib.metadata.version('nwbinspector')`."
)

warnings.warn(message=message, category=DeprecationWarning, stacklevel=2)

# Still keep imports functional with warning for soft deprecation cycle
# TODO: remove after 9/15/2024
from .._version import __version__
