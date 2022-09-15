"""Helper functions for internal use across the testing suite."""
import os
from distutils.util import strtobool
from typing import Tuple, Optional

from .tools import check_streaming_enabled
from .utils import is_module_installed


def check_streaming_tests_enabled() -> Tuple[bool, Optional[str]]:
    """
    General purpose helper for determining if the testing environment can support S3 DANDI streaming.

    Returns the boolean status of the check and, if False, provides a string reason for the failure for the user to
    utilize as they please (raise an error or warning with that message, print it, or ignore it).
    """
    failure_reason = ""

    environment_skip_flag = os.environ.get("NWBI_SKIP_NETWORK_TESTS", "")
    environment_skip_flag_bool = (
        strtobool(os.environ.get("NWBI_SKIP_NETWORK_TESTS", "")) if environment_skip_flag != "" else False
    )
    if environment_skip_flag_bool:
        failure_reason += "Environmental variable set to skip network tets."

    streaming_enabled, streaming_failure_reason = check_streaming_enabled()
    if not streaming_enabled:
        failure_reason += streaming_failure_reason

    have_dandi = is_module_installed("dandi")
    if not have_dandi:
        failure_reason += "The DANDI package is not installed on the system."

    failure_reason = None if failure_reason == "" else failure_reason
    return streaming_enabled and not environment_skip_flag_bool and have_dandi, failure_reason
