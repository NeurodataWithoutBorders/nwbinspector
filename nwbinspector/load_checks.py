"""Authors: Cody Baker and Ben Dichter."""
from .utils import available_checks
from . import (
    check_dataset_compression,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)


def load_checks(checks=available_checks):
    return available_checks
