"""Helper functions related to DANDI for internal use that rely on external dependencies (i.e., dandi)."""

import pathlib
import re
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Literal, Optional, Union

from ..utils import calculate_number_of_cpu, is_module_installed


def get_s3_urls_and_dandi_paths(
    dandiset_id: str,
    version_id: Optional[str] = None,
    n_jobs: int = 1,
    client: Union["dandi.dandiapi.DandiAPIClient", None] = None,  # type: ignore
) -> dict[str, str]:
    """
    Collect S3 URLS from a DANDISet ID.

    Returns dictionary that maps each S3 url to the displayed file path on the DANDI archive content page.

    Parameters
    ----------
    dandiset_id : str
        The six-digit identifier of the Dandiset.
    version_id : str, optional
        The version of the Dandiset. Defaults to the latest published version, or "draft" if none exist.
    n_jobs : int, optional
        Number of processes used to resolve the content URLs. Defaults to 1 (no parallelism).
    client : dandi.dandiapi.DandiAPIClient, optional
        The client object can be passed to avoid re-instantiation over an iteration.
    """
    assert re.fullmatch(
        pattern="^[0-9]{6}$", string=dandiset_id
    ), "The specified 'path' is not a proper DANDISet ID. It should be a six-digit numeric identifier."

    if client is not None:
        return _collect_s3_urls_and_dandi_paths(
            client=client, dandiset_id=dandiset_id, version_id=version_id, n_jobs=n_jobs
        )

    assert is_module_installed(module_name="dandi"), "You must install DANDI to get S3 paths (pip install dandi)."
    from dandi.dandiapi import DandiAPIClient

    with DandiAPIClient() as client:
        return _collect_s3_urls_and_dandi_paths(
            client=client, dandiset_id=dandiset_id, version_id=version_id, n_jobs=n_jobs
        )


def _collect_s3_urls_and_dandi_paths(
    client: "dandi.dandiapi.DandiAPIClient",  # type: ignore
    dandiset_id: str,
    version_id: Optional[str],
    n_jobs: int,
) -> dict[str, str]:
    """Resolve the content URL of every NWB asset in the Dandiset, in parallel if requested."""
    n_jobs = calculate_number_of_cpu(requested_cpu=n_jobs)

    dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=version_id)
    nwb_assets = [asset for asset in dandiset.get_assets() if asset.path.split(".")[-1] == "nwb"]

    s3_urls_to_dandi_paths: dict[str, str] = dict()
    if n_jobs == 1:
        for asset in nwb_assets:
            s3_urls_to_dandi_paths.update(_get_content_url_and_path(asset=asset))
        return s3_urls_to_dandi_paths

    max_workers = n_jobs if n_jobs > 0 else None
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit every asset before collecting any result, so that requests actually overlap
        futures = [
            executor.submit(_get_content_url_and_path, asset=asset, follow_redirects=1, strip_query=True)
            for asset in nwb_assets
        ]
        for future in as_completed(futures):
            s3_urls_to_dandi_paths.update(future.result())

    return s3_urls_to_dandi_paths


def _get_content_url_and_path(
    asset: "dandi.dandiapi.BaseRemoteAsset",  # type: ignore
    follow_redirects: int = 1,
    strip_query: bool = True,
) -> dict[str, str]:
    """
    Private helper function for parallelization in 'get_s3_urls_and_dandi_paths'.

    Must be globally defined (not as a part of get_s3_urls..) in order to be pickled.
    """
    return {asset.get_content_url(follow_redirects=follow_redirects, strip_query=strip_query): asset.path}


def get_nwb_assets_from_dandiset(
    dandiset_id: str,
    dandiset_version: Union[str, Literal["draft"], None] = None,
    client: Union["dandi.dandiapi.DandiAPIClient", None] = None,  # type: ignore
) -> list["dandi.dandiapi.BaseRemoteAsset"]:  # type: ignore
    """
    Collect NWB assets from a DANDISet ID.

    Returns list of NWB assets.
    """
    if client is None:
        import dandi.dandiapi

        client = dandi.dandiapi.DandiAPIClient()

    dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=dandiset_version)

    nwb_assets = [asset for asset in dandiset.get_assets() if ".nwb" in pathlib.Path(asset.path).suffixes]

    return nwb_assets
