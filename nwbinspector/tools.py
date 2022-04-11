"""Helper functions for internal use that rely on external dependencies (i.e., pynwb)."""
import re
from uuid import uuid4
from datetime import datetime
from typing import Optional
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


def get_s3_urls(dandiset_id: str, version_id: Optional[str] = None, n_jobs: int = 1):
    """Auxilliary function for collecting S3 URLS from a DANDISet ID."""
    assert re.fullmatch(
        pattern="^[0-9]{6}$", string=dandiset_id
    ), "The specified 'path' is not a proper DANDISet ID. It should be a six-digit numeric identifier."

    s3_urls = []
    if n_jobs == 1:
        with DandiAPIClient() as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            for asset in dandiset.get_assets():
                asset = dandiset.get_asset_by_path(asset.path)
                s3_urls.append(asset.get_content_url(follow_redirects=1, strip_query=True))
    else:
        with DandiAPIClient() as client:
            dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
            max_workers = n_jobs if n_jobs > 0 else None
            with ProcessPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for asset in dandiset.get_assets():
                    futures.append(executor.submit(asset.get_content_url, follow_redirects=1, strip_query=True))
                for future in as_completed(futures):
                    s3_urls.append(future.result())
    return s3_urls
