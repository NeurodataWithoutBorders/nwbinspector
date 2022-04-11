"""Helper functions for internal use that rely on external dependencies (i.e., pynwb)."""
import re
from uuid import uuid4
from datetime import datetime
from typing import Optional, Dict
from concurrent.futures import ProcessPoolExecutor, as_completed

from pynwb import NWBFile
from dandi.dandiapi import DandiAPIClient


def make_minimal_nwbfile():
    """Most basic NWBFile that can exist."""
    return NWBFile(session_description="", identifier=str(uuid4()), session_start_time=datetime.now().astimezone())


def all_of_type(nwbfile: NWBFile, neurodata_type):
    """Iterate over all objects inside an NWBFile object and return those that match the given neurodata_type."""
    for obj in nwbfile.objects.values():
        if isinstance(obj, neurodata_type):
            yield obj


def get_s3_urls_and_dandi_paths(
    dandiset_id: str, version_id: Optional[str] = None, api_url: Optional[str] = None, n_jobs: int = 1
) -> Dict[str, str]:
    """
    Collect S3 URLS from a DANDISet ID.

    Returns dictionary that maps each S3 url to the displayed file path on the DANDI archive content page.

    If using the staging server, pass api_url=https://api-staging.dandiarchive.org/api
    """
    assert re.fullmatch(
        pattern="^[0-9]{6}$", string=dandiset_id
    ), "The specified 'path' is not a proper DANDISet ID. It should be a six-digit numeric identifier."

    s3_urls_to_dandi_paths = dict()
    if n_jobs != 1:
        with DandiAPIClient(api_url=api_url) as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            max_workers = n_jobs if n_jobs > 0 else None
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for asset in dandiset.get_assets():
                    futures.append(
                        executor.submit(_get_content_url_and_path, asset=asset, follow_redirects=1, strip_query=True)
                    )
                for future in as_completed(futures):
                    s3_urls_to_dandi_paths.update(future.result())
    else:
        with DandiAPIClient(api_url=api_url) as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            for asset in dandiset.get_assets():
                s3_urls_to_dandi_paths.update(_get_content_url_and_path(asset=asset))
    return s3_urls_to_dandi_paths


def _get_content_url_and_path(
    asset, api_url: Optional[str] = None, follow_redirects: int = 1, strip_query: bool = True
):
    """Private helper function for parallelization in 'get_s3_urls_and_dandi_paths'."""
    if api_url:
        # The DANDIAPIClient.get_dandiset is setting the api_url correctly, but the assets from
        # DANDIAPIClient.get_dandiset.get_asset do not propagate it
        asset_url = api_url + "/assets/" + asset.blob + "/download/"
    else:
        asset_url = asset.get_content_url(follow_redirects=1, strip_query=True)
    return {asset_url: asset.path}
