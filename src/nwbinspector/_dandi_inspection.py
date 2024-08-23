import pathlib
from typing import Union, Iterable, Literal, List

import h5py
import pynwb

from ._types import InspectorMessage, Importance
from ._nwb_inspection import inspect_nwbfile_object


def inspect_dandiset(
    *,
    dandiset_id: str,
    dandiset_version: Union[str, Literal["draft"], None] = None,
    checks: Union[list, None] = None,
    ignore: Union[List[str], None] = None,
    select: Union[List[str], None] = None,
    importance_threshold: Union[str, Importance] = Importance.BEST_PRACTICE_SUGGESTION,
    skip_validate: bool = False,
    show_progress_bar: bool = True,
    client: Union["dandi.dandiapi.DandiAPIClient", None] = None,
) -> Iterable[InspectorMessage]:
    """
    Inspect a Dandiset for common issues.

    Parameters
    ----------
    dandiset_id : six-digit string, "draft", or None
        The six-digit ID of the Dandiset to inspect.
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
    skip_validate : bool, default: False
        Skip the PyNWB validation step.
        This may be desired for older NWBFiles (< schema version v2.10).
    show_progress_bar : bool, optional
        Whether to display a progress bar while scanning the assets on the Dandiset.
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

    nwb_assets = [asset for asset in dandiset.get_assets() if ".nwb" in pathlib.Path(asset.path).suffixes]

    nwb_assets_iterator = nwb_assets
    if show_progress_bar is True:
        import tqdm

        nwb_assets_iterator = tqdm.tqdm(
            iterable=nwb_assets, total=len(nwb_assets), desc="Inspecting NWB files", unit="file", position=0, leave=True
        )

    for asset in nwb_assets_iterator:
        dandi_s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)

        yield _insect_dandi_s3_nwb(
            dandi_s3_url=dandi_s3_url,
            dandiset_id=dandiset_id,
            dandiset_version=dandiset_version,
            checks=checks,
            ignore=ignore,
            select=select,
            importance_threshold=importance_threshold,
            skip_validate=skip_validate,
            client=client,
        )

    pass


def inspect_dandi_file_path(
    *,
    dandi_file_path: str,
    dandiset_id: str,
    dandiset_version: Union[str, Literal["draft"], None] = None,
    checks: Union[list, None] = None,
    ignore: Union[List[str], None] = None,
    select: Union[List[str], None] = None,
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
    skip_validate: bool = False,
) -> Iterable[InspectorMessage]:
    import remfile

    byte_stream = remfile.File(url=dandi_s3_url)
    file = h5py.File(name=byte_stream)
    io = pynwb.NWBHDF5IO(file=file)

    if skip_validate is False:
        validation_errors = pynwb.validate(io=io)

        for validation_error in validation_errors:
            yield InspectorMessage(
                message=validation_error.reason,
                importance=Importance.PYNWB_VALIDATION,
                check_function_name=validation_error.name,
                location=validation_error.location,
                file_path=nwbfile_path,
            )

    nwbfile = io.read()

    yield inspect_nwbfile_object(
        nwbfile_object=nwbfile,
        checks=checks,
        config="dandi",
        ignore=ignore,
        select=select,
        importance_threshold=importance_threshold,
    )
