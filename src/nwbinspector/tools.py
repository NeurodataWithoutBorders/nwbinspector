"""Helper functions for internal use that rely on external dependencies (i.e., pynwb)."""
import re
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict, Tuple
from concurrent.futures import ProcessPoolExecutor, as_completed
from urllib import request
from warnings import warn

import h5py
from pynwb import NWBFile

from .utils import is_module_installed, calculate_number_of_cpu


def make_minimal_nwbfile():
    """Most basic NWBFile that can exist."""
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())


def all_of_type(nwbfile: NWBFile, neurodata_type):
    """Iterate over all objects inside an NWBFile object and return those that match the given neurodata_type."""
    for obj in nwbfile.objects.values():
        if isinstance(obj, neurodata_type):
            yield obj


def get_nwbfile_path_from_internal_object(obj):
    """Determine the file path on disk for a NWBFile given only an internal object of that file."""
    if isinstance(obj, NWBFile):
        return obj.container_source
    return obj.get_ancestor("NWBFile").container_source


def get_s3_urls_and_dandi_paths(dandiset_id: str, version_id: Optional[str] = None, n_jobs: int = 1) -> Dict[str, str]:
    """
    Collect S3 URLS from a DANDISet ID.

    Returns dictionary that maps each S3 url to the displayed file path on the DANDI archive content page.
    """
    assert is_module_installed(module_name="dandi"), "You must install DANDI to get S3 paths (pip install dandi)."
    from dandi.dandiapi import DandiAPIClient

    assert re.fullmatch(
        pattern="^[0-9]{6}$", string=dandiset_id
    ), "The specified 'path' is not a proper DANDISet ID. It should be a six-digit numeric identifier."

    s3_urls_to_dandi_paths = dict()
    n_jobs = calculate_number_of_cpu(requested_cpu=n_jobs)
    if n_jobs != 1:
        with DandiAPIClient() as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            max_workers = n_jobs if n_jobs > 0 else None
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for asset in dandiset.get_assets():
                    if asset.path.split(".")[-1] == "nwb":
                        futures.append(
                            executor.submit(
                                _get_content_url_and_path, asset=asset, follow_redirects=1, strip_query=True
                            )
                        )
                    for future in as_completed(futures):
                        s3_urls_to_dandi_paths.update(future.result())
    else:
        with DandiAPIClient() as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            for asset in dandiset.get_assets():
                if asset.path.split(".")[-1] == "nwb":
                    s3_urls_to_dandi_paths.update(_get_content_url_and_path(asset=asset))
    return s3_urls_to_dandi_paths


def _get_content_url_and_path(asset, follow_redirects: int = 1, strip_query: bool = True) -> Dict[str, str]:
    """
    Private helper function for parallelization in 'get_s3_urls_and_dandi_paths'.

    Must be globally defined (not as a part of get_s3_urls..) in order to be pickled.
    """
    return {asset.get_content_url(follow_redirects=1, strip_query=True): asset.path}


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
