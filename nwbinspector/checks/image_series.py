"""Check functions specific to ImageSeries."""
from pathlib import Path

from pynwb.image import ImageSeries

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.CRITICAL, neurodata_type=ImageSeries)
def check_image_series_external_file(image_series: ImageSeries):
    """Check if the external_file specified by an ImageSeries actually exists at the relative location."""
    if image_series.external_file is None:
        return
    for file_path in image_series.external_file:
        if not Path(file_path).exists():
            yield InspectorMessage(
                message="The external file does not exist. Please confirm the relative location to the NWBFile."
            )
