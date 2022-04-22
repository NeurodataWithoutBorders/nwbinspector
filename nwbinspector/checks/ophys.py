"""Check functions specific to optical electrophysiology neurodata types."""
from pynwb.ophys import (
    RoiResponseSeries,
    PlaneSegmentation,
    OpticalChannel,
    ImagingPlane,
)

from hdmf.utils import get_data_shape

from ..register_checks import register_check, Importance, InspectorMessage

MIN_LAMBDA = 10.0  # trigger warnings for wavelength values less than this value


@register_check(importance=Importance.CRITICAL, neurodata_type=RoiResponseSeries)
def check_roi_response_series_dims(roi_response_series: RoiResponseSeries):
    """Check the dimensions of an ROI series to ensure the time axis is the correct dimension."""
    data = roi_response_series.data
    rois = roi_response_series.rois

    data_shape = get_data_shape(data, strict_no_data_load=True)

    if data_shape and len(data_shape) == 2 and data_shape[1] != len(rois.data):
        if data_shape[0] == len(rois.data):
            return InspectorMessage(
                message=(
                    "The second dimension of data does not match the length of rois, "
                    "but instead the first does. Data is oriented incorrectly and should be transposed."
                )
            )
        return InspectorMessage(
            message="The second dimension of data does not match the length of rois. Your data may be transposed."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=RoiResponseSeries)
def check_roi_response_series_link_to_plane_segmentation(
    roi_response_series: RoiResponseSeries,
):
    """Check that each ROI response series links to a plane segmentation."""
    if not isinstance(roi_response_series.rois.table, PlaneSegmentation):
        return InspectorMessage(message="rois field does not point to a PlaneSegmentation table.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=OpticalChannel)
def check_emission_lambda_in_nm(optical_channel: OpticalChannel):
    """Check that emission lambda is in feasible range for unit nanometers."""
    if optical_channel.emission_lambda < MIN_LAMBDA:
        return InspectorMessage(f"emission lambda of {optical_channel.emission_lambda} should be in units of nm.")


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImagingPlane)
def check_excitation_lambda_in_nm(imaging_plane: ImagingPlane):
    """Check that emission lambda is in feasible range for unit nanometers."""
    if imaging_plane.excitation_lambda < MIN_LAMBDA:
        return InspectorMessage(f"excitation lambda of {imaging_plane.excitation_lambda} should be in units of nm.")
