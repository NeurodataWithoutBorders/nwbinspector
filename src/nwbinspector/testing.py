"""Helper functions for internal use across the testing suite."""
import os
from distutils.util import strtobool
from typing import Tuple, Optional

from packaging.version import Version

from .tools import check_streaming_enabled
from .utils import is_module_installed, get_package_version


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


def generate_testing_files():  # pragma: no cover
    assert get_package_version(name="pynwb") == Version("2.1.0"), "Generating the testing files requires PyNWB v2.1.0!"
    
    test_config_file_path = Path(__file__).parent.parent.parent / "tests" / "test_config.json"
    with open(file=test_config_file_path) as file:
        test_config = json.loads(file)
    
    local_path = Path(test_config["LOCAL_PATH"])
    local_path.mkdir(exist_ok=True)
    
    with NWBHDF5IO(path=local_path / "image_series_test_file.nwb", mode="w") as io:
        nwbfile = make_minimal_nwbfile()
        ## TODO
        io.write(nwbfile)
