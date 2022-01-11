"""Authors: Cody Baker and Ben Dichter."""
from .utils import default_checks
from .check_datasets import check_dataset_compression
from .check_time_series import check_regular_timestamps, check_data_orientation


def load_checks(checks=default_checks):
    return default_checks
