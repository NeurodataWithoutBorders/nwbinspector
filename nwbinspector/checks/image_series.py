"""Check functions specific to ImageSeries."""
from pathlib import Path

from pynwb.image import ImageSeries

from ..register_checks import register_check, Importance, InspectorMessage
from ..tools import get_nwbfile_path_from_internal_object


@register_check(importance=Importance.CRITICAL, neurodata_type=ImageSeries)
def check_image_series_external_file_valid(image_series: ImageSeries):
    """Check if the external_file specified by an ImageSeries actually exists."""
    if image_series.external_file is None:
        return
    nwbfile_path = Path(get_nwbfile_path_from_internal_object(obj=image_series))
    for file_path in image_series.external_file:
        file_path = file_path.decode() if isinstance(file_path, bytes) else file_path
        if not Path(file_path).is_absolute() and not (nwbfile_path.parent / file_path).exists():
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' does not exist. Please confirm the relative location to the"
                    " NWBFile."
                )
            )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_image_series_external_file_relative(image_series: ImageSeries):
    """Check if the external_file specified by an ImageSeries, if it exists, is relative."""
    if image_series.external_file is None:
        return
    for file_path in image_series.external_file:
        file_path = file_path.decode() if isinstance(file_path, bytes) else file_path
        if Path(file_path).is_absolute():
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' is not a relative path. "
                    "Please adjust the absolute path to be relative to the location of the NWBFile."
                )
            )
