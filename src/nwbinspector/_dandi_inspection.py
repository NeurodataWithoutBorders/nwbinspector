import pathlib
from typing import Union, Iterable, Literal

import h5py
import pynwb

from ._types import InspectorMessage, Importance
from ._nwb_inspection import inspect_nwbfile_object


def inspect_dandiset(
    *,
    dandiset_id: str,
    dandiset_version: Union[str, Literal["draft"], None] = None,
    checks: Optional[list] = None,
    ignore: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
    client: Union["dandi.dandiapi.DandiAPIClient", None] = None,
) -> Iterable[InspectorMessage]:
    """
    Inspect a Dandiset for common issues.

    Parameters
    ----------
    dandiset_id : six-digit string, "draft", or None
        The six-digit ID of the Dandiset.
    dandiset_version : string
        The specific published version of the Dandiset to inspect.
        If None, the latest version is used.
        If there are no published versions, then 'draft' is used instead.
    checks : list, optional
        list of checks to run
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
        Names of functions to pick out of available checks.
    importance_threshold : string or Importance, optional
        Ignores tests with an assigned importance below this threshold.
        Importance has three levels:

            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation

        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    client: dandi.dandiapi.DandiAPIClient
        The client object can be passed to avoid re-instantiation over an iteration.
    """
    if client is None:
        import dandi.dandiapi

        client = dandi.dandiapi.DandiAPIClient()

    dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=dandiset_version)

    if not any(
        asset_type.get("identifier", "") != "RRID:SCR_015242"  # Identifier for NWB standard
        for asset_type in dandiset.get_raw_metadata().get("assetsSummary", {}).get("dataStandard", [])
    ):
        yield iter([])

    for asset in dandiset.get_assets():
        if ".nwb" not in pathlib.Path(asset.path).suffixes:
            continue

        dandi_s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)
        yield _insect_dandi_s3_nwb(
            dandi_s3_url=dandi_s3_url,
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            checks=checks,
            ignore=ignore,
            select=select,
            importance_threshold=importance_threshold,
            client=client,
        )

    pass


def inspect_dandi_file_path(
    *,
    dandi_file_path: str,
    dandiset_id: str,
    dandiset_version: Union[str, Literal["draft"], None] = None,
    checks: Optional[list] = None,
    ignore: Optional[List[str]] = None,
    select: Optional[List[str]] = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
    client: Union["dandi.dandiapi.DandiAPIClient", None] = None,
) -> Iterable[InspectorMessage]:
    """
    Inspect a Dandifile for common issues.

    Parameters
    ----------
    dandi_file_path : string
        The path to the Dandifile as seen on the archive; e.g., 'sub-123_ses-456+ecephys.nwb'.
    dandiset_id : six-digit string, "draft", or None
        The six-digit ID of the Dandiset.
    dandiset_version : string
        The specific published version of the Dandiset to inspect.
        If None, the latest version is used.
        If there are no published versions, then 'draft' is used instead.
    checks : list, optional
        list of checks to run
    ignore: list, optional
        Names of functions to skip.
    select: list, optional
        Names of functions to pick out of available checks.
    importance_threshold : string or Importance, optional
        Ignores tests with an assigned importance below this threshold.
        Importance has three levels:

            CRITICAL
                - potentially incorrect data
            BEST_PRACTICE_VIOLATION
                - very suboptimal data representation
            BEST_PRACTICE_SUGGESTION
                - improvable data representation

        The default is the lowest level, BEST_PRACTICE_SUGGESTION.
    client: dandi.dandiapi.DandiAPIClient
        The client object can be passed to avoid re-instantiation over an iteration.
    """
    if client is None:
        import dandi.dandiapi

        client = dandi.dandiapi.DandiAPIClient()

    dandiset = client.get_dandiset(dandiset_id=dandiset_id, version_id=dandiset_version)
    asset = dandiset.get_asset_by_path(path=dandi_file_path)
    dandi_s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

    yield _insect_dandi_s3_nwb(
        dandi_s3_url=dandi_s3_url,
        checks=checks,
        ignore=ignore,
        select=select,
        importance_threshold=importance_threshold,
        client=client,
    )


def _insect_dandi_s3_nwb(
    *,
    dandi_s3_url: str,
    checks: Union[list, None] = None,
    ignore: Union[List[str], None] = None,
    select: Union[List[str], None] = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
) -> Iterable[InspectorMessage]:
    import remfile

    byte_stream = remfile.File(url=dandi_s3_url)
    file = h5py.File(name=byte_stream)
    io = pynwb.NWBHDF5IO(file=file)
    nwbfile = io.read()

    yield inspect_nwbfile_object(
        nwbfile_object=nwbfile,
        checks=checks,
        config="dandi",
        ignore=ignore,
        select=select,
        importance_threshold=importance_threshold,
    )
