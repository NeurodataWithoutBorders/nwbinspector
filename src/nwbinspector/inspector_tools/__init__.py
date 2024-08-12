import warnings

message = (
    "The 'inspector_tools' module has been deprecated. Please import the helper functions from the top-level package."
)

warnings.warn(message=message, category=DeprecationWarning)
