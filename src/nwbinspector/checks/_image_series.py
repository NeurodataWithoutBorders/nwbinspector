"""Check functions specific to ImageSeries."""

from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Optional

from pynwb.image import ImageSeries
from pynwb.ophys import TwoPhotonSeries

from .._registration import Importance, InspectorMessage, register_check
from ..tools import get_nwbfile_path_from_internal_object


@register_check(importance=Importance.CRITICAL, neurodata_type=ImageSeries)
def check_image_series_external_file_valid(image_series: ImageSeries) -> Optional[Iterable[InspectorMessage]]:
    """
    Check if the external_file specified by an ImageSeries actually exists.

    Best Practice: :ref:`best_practice_use_external_mode`
    """
    if image_series.external_file is None:
        return None
    nwbfile_path = Path(get_nwbfile_path_from_internal_object(neurodata_object=image_series))
    for file_path in image_series.external_file:
        file_path = file_path.decode() if isinstance(file_path, bytes) else file_path
        if not Path(file_path).is_absolute() and not (nwbfile_path.parent / file_path).exists():
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' does not exist. Please confirm the relative location to the"
                    " NWBFile."
                )
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_image_series_external_file_relative(image_series: ImageSeries) -> Optional[Iterable[InspectorMessage]]:
    """
    Check if the external_file specified by an ImageSeries, if it exists, is relative.

    Best Practice: :ref:`best_practice_use_external_mode`
    """
    if image_series.external_file is None:
        return None
    for file_path in image_series.external_file:
        file_path = file_path.decode() if isinstance(file_path, bytes) else file_path
        if PureWindowsPath(file_path).is_absolute() or PurePosixPath(file_path).is_absolute():
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' is not a relative path. "
                    "Please adjust the absolute path to be relative to the location of the NWBFile."
                )
            )

    return None


RECOMMENDED_LOSSY_CONTAINERS = (".mp4", ".webm")
RECOMMENDED_LOSSY_CODECS = ("h264", "vp8", "vp9", "av1")
RECOMMENDED_LOSSLESS_CODECS = ("ffv1",)


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=ImageSeries)
def check_image_series_external_file_format(image_series: ImageSeries) -> Optional[Iterable[InspectorMessage]]:
    """
    Check if the external_file of an ImageSeries uses a standard video container and codec.

    Best Practice: :ref:`best_practice_external_file_format`
    """
    # False positive case; TwoPhotonSeries are a subclass of ImageSeries, but their external files are imaging
    # data such as TIFF stacks rather than video
    if isinstance(image_series, TwoPhotonSeries) or image_series.external_file is None:
        return None
    try:
        import av
    except ImportError:  # the format cannot be read without PyAV, so nothing can be said about it
        return None

    nwbfile_path = Path(get_nwbfile_path_from_internal_object(neurodata_object=image_series))
    for file_path in image_series.external_file:
        file_path = file_path.decode() if isinstance(file_path, bytes) else file_path
        resolved_path = Path(file_path) if Path(file_path).is_absolute() else nwbfile_path.parent / file_path
        if not resolved_path.exists():  # reported by check_image_series_external_file_valid
            continue
        try:
            with av.open(str(resolved_path)) as container:
                if not container.streams.video:
                    continue
                codec = container.streams.video[0].codec_context.codec.canonical_name
        except av.FFmpegError:  # not a media file, or one that cannot be opened
            continue

        if codec not in RECOMMENDED_LOSSY_CODECS and codec not in RECOMMENDED_LOSSLESS_CODECS:
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' uses the '{codec}' codec, which is not one of the standard "
                    "video codecs. Please use H.264, VP8, VP9 or AV1 in an MP4 or WebM container, or FFV1 if the "
                    "video has to stay lossless. Note that H.264 is covered by patents while VP8, VP9 and AV1 are "
                    "royalty-free."
                )
            )
            continue  # the re-encoding settles the container as well

        if codec in RECOMMENDED_LOSSLESS_CODECS:
            continue  # every tool that reads FFV1 handles its containers alike, so the container gains nothing

        suffix = PurePosixPath(file_path).suffix.lower()
        if suffix not in RECOMMENDED_LOSSY_CONTAINERS:
            yield InspectorMessage(
                message=(
                    f"The external file '{file_path}' uses the '{suffix}' container, which is not a standard "
                    "container for sharing video. Please use MP4 or WebM instead. The codec is already a "
                    "recommended one, so the container can be changed without re-encoding: "
                    f"ffmpeg -i {file_path} -c copy output.mp4"
                )
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_image_series_data_size(image_series: ImageSeries, gb_lower_bound: float = 20.0) -> Optional[InspectorMessage]:
    """
    Check if an ImageSeries stored is larger than gb_lower_bound and suggests external file.

    Best Practice: :ref:`best_practice_use_external_mode`
    """
    # False positive case; TwoPhotonSeries are a subclass of ImageSeries, but it is very common and perfectly fine
    # to write lots of data using one without an external file
    if isinstance(image_series, TwoPhotonSeries):
        return None

    data = image_series.data

    if getattr(data, "compression", None) is not None:
        data_size_gb = data.id.get_storage_size() / 1e9
    else:
        data_size_gb = data.size * data.dtype.itemsize / 1e9

    if data_size_gb > gb_lower_bound:
        return InspectorMessage(message="ImageSeries is very large. Consider using external mode for better storage.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_image_series_starting_frame_without_external_file(image_series: ImageSeries) -> Optional[InspectorMessage]:
    """
    Check if starting_frame is set when external_file is not used.

    The starting_frame attribute is only relevant when using external files.
    If there is no external file, there should be no starting_frame.

    Best Practice: :ref:`best_practice_starting_frame_only_with_external_file`
    """
    if (
        image_series.external_file is None
        and image_series.starting_frame is not None
        and len(image_series.starting_frame) > 0
    ):
        return InspectorMessage(
            message="ImageSeries has starting_frame set but no external_file. "
            "starting_frame is only relevant when using external files."
        )

    return None
