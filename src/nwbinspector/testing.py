"""Helper functions for internal use across the testing suite."""
import os
import json
from distutils.util import strtobool
from pathlib import Path
from typing import Tuple, Optional

from packaging.version import Version
from pynwb import NWBHDF5IO
from pynwb.image import ImageSeries

from .tools import check_streaming_enabled, make_minimal_nwbfile
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


def load_testing_config() -> dict:
    """Helper function for loading the testing configuration file as a dictionary."""
    test_config_file_path = Path(__file__).parent.parent.parent / "tests" / "testing_config.json"

    # This error would only occur if someone installed a previous version
    # directly from GitHub and then updated the branch/commit in-place
    if not test_config_file_path.exists():  # pragma: no cover
        raise FileNotFoundError(
            "The testing configuration file not found at the location '{test_config_file_path}'! "
            "Please try reinstalling the package."
        )

    with open(file=test_config_file_path) as file:
        test_config = json.load(file)

    return test_config


def update_testing_config(key: str, value):
    """Update a key/value pair in the testing configuration file through the API."""
    test_config_file_path = Path(__file__).parent.parent.parent / "tests" / "testing_config.json"

    testing_config = load_testing_config()

    if key not in testing_config:
        raise KeyError("Updating the testing configuration file via the API is only possible for the pre-defined keys!")
    testing_config[key] = value

    with open(file=test_config_file_path, mode="w") as file:
        json.dump(testing_config, file)


def generate_testing_files():  # pragma: no cover
    """Generate a local copy of the NWB files required for all tests."""
    generate_image_series_testing_files()


def generate_image_series_testing_files():  # pragma: no cover
    """Generate a local copy of the NWB files required for the image series tests."""
    assert get_package_version(name="pynwb") == Version("2.1.0"), "Generating the testing files requires PyNWB v2.1.0!"

    testing_config = load_testing_config()

    local_path = Path(testing_config["LOCAL_PATH"])
    local_path.mkdir(exist_ok=True, parents=True)

    movie_1_file_path = local_path / "temp_movie_1.mov"
    nested_folder = local_path / "nested_folder"
    nested_folder.mkdir(exist_ok=True)
    movie_2_file_path = nested_folder / "temp_movie_2.avi"
    for file_path in [movie_1_file_path, movie_2_file_path]:
        with open(file=file_path, mode="w") as file:
            file.write("Not a movie file, but at least it exists.")
    nwbfile = make_minimal_nwbfile()
    nwbfile.add_acquisition(
        ImageSeries(
            name="TestImageSeriesGoodExternalPaths",
            rate=1.0,
            external_file=[
                "/".join([".", movie_1_file_path.name]),
                "/".join([".", nested_folder.name, movie_2_file_path.name]),
            ],
        )
    )
    nwbfile.add_acquisition(
        ImageSeries(
            name="TestImageSeriesExternalPathDoesNotExist",
            rate=1.0,
            external_file=["madeup_file.mp4"],
        )
    )
    absolute_file_path = str(Path("madeup_file.mp4").absolute())
    nwbfile.add_acquisition(
        ImageSeries(name="TestImageSeriesExternalPathIsNotRelative", rate=1.0, external_file=[absolute_file_path])
    )
    with NWBHDF5IO(path=local_path / "image_series_testing_file.nwb", mode="w") as io:
        io.write(nwbfile)
