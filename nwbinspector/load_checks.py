"""Authors: Cody Baker and Ben Dichter."""
from copy import deepcopy

from .utils import default_checks
from .check_time_series import (
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
)


def load_checks(checks=deepcopy(default_checks)):
    return default_checks
