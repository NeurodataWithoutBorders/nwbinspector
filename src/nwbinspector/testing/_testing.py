"""Helper functions for internal use across the testing suite."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from urllib import request
from uuid import uuid4

import h5py
from hdmf.backends.hdf5 import HDF5IO
from hdmf.backends.io import HDMFIO
from packaging.version import Version
from pynwb import NWBHDF5IO, NWBFile
from pynwb.image import ImageSeries

from ..utils import get_package_version, is_module_installed, strtobool

# The tests must be invoked at the outer level of the repository
TESTING_CONFIG_FILE_PATH = Path.cwd() / "tests" / "testing_config.json"


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
    # This error would only occur if someone installed a previous version
    # directly from GitHub and then updated the branch/commit in-place
    if not TESTING_CONFIG_FILE_PATH.exists():  # pragma: no cover
        raise FileNotFoundError(
            f"The testing configuration file not found at the location '{TESTING_CONFIG_FILE_PATH}'! "
            "Please try reinstalling the package."
        )

    with open(file=TESTING_CONFIG_FILE_PATH) as file:
        test_config = json.load(file)

    return test_config


def update_testing_config(key: str, value):
    """Update a key/value pair in the testing configuration file through the API."""
    testing_config = load_testing_config()

    if key not in testing_config:
        raise KeyError("Updating the testing configuration file via the API is only possible for the pre-defined keys!")
    testing_config[key] = value

    with open(file=TESTING_CONFIG_FILE_PATH, mode="w") as file:
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


def make_minimal_nwbfile():
    """
    Most basic NWBFile that can exist.

    TODO: replace with pynwb.mock if we can require minimal PyNWB version (or perhaps just for a testing)
    """
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())


def check_streaming_enabled() -> Tuple[bool, Optional[str]]:
    """
    General purpose helper for determining if the environment can support S3 DANDI streaming.

    Returns the boolean status of the check and, if False, provides a string reason for the failure for the user to
    utilize as they please (raise an error or warning with that message, print it, or ignore it).
    """
    try:
        request.urlopen("https://dandiarchive.s3.amazonaws.com/ros3test.nwb", timeout=1)
    except request.URLError:
        return False, "Internet access to DANDI failed."
    if "ros3" not in h5py.registered_drivers():
        return False, "ROS3 driver not installed."
    return True, None


def check_hdf5_io_open(io: HDF5IO):
    """Check if an h5py.File object is open by using the file object's .id attribute, which is invalid when the file is closed."""
    return io._file.id.valid


def check_zarr_io_open(io: HDMFIO):
    """For Zarr, the private attribute `_ZarrIO__file` is set to a `zarr.group` on open."""
    import zarr  # relative import since extra requirement

    return isinstance(io._ZarrIO__file, zarr.Group)
