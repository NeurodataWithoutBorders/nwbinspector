"""Check functions specific to optical electrophysiology neurodata types."""

from typing import Iterable, Optional

from pynwb.image import ImageSeries
from pynwb.ophys import (
    ImagingPlane,
    OpticalChannel,
    PlaneSegmentation,
    RoiResponseSeries,
)

from ._common import MOUSE_SPECIES_VALUES
from .._internal_configs._allen_ccf import get_allen_ccf_location_terms
from .._registration import Importance, InspectorMessage, register_check
from ..utils import get_data_shape

MIN_LAMBDA = 10.0  # trigger warnings for wavelength values less than this value


@register_check(importance=Importance.CRITICAL, neurodata_type=RoiResponseSeries)
def check_roi_response_series_dims(roi_response_series: RoiResponseSeries) -> Optional[InspectorMessage]:
    """
    Check the dimensions of an ROI series to ensure the time axis is the correct dimension.

    Best Practice: :ref:`best_practice_data_orientation`
    """
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

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=RoiResponseSeries)
def check_roi_response_series_link_to_plane_segmentation(
    roi_response_series: RoiResponseSeries,
) -> Optional[InspectorMessage]:
    """
    Check that each ROI response series links to a plane segmentation.

    Best Practice: TODO
    """
    if not isinstance(roi_response_series.rois.table, PlaneSegmentation):
        return InspectorMessage(message="rois field does not point to a PlaneSegmentation table.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=OpticalChannel)
def check_emission_lambda_in_nm(optical_channel: OpticalChannel) -> Optional[InspectorMessage]:
    """
    Check that emission lambda is in feasible range for unit nanometers.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if optical_channel.emission_lambda < MIN_LAMBDA:
        return InspectorMessage(f"emission lambda of {optical_channel.emission_lambda} should be in units of nm.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImagingPlane)
def check_excitation_lambda_in_nm(imaging_plane: ImagingPlane) -> Optional[InspectorMessage]:
    """
    Check that emission lambda is in feasible range for unit nanometers.

    Best Practice: :ref:`best_practice_unit_of_measurement`
    """
    if imaging_plane.excitation_lambda < MIN_LAMBDA:
        return InspectorMessage(f"excitation lambda of {imaging_plane.excitation_lambda} should be in units of nm.")

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=PlaneSegmentation)
def check_plane_segmentation_image_mask_shape_against_ref_images(
    plane_segmentation: PlaneSegmentation,
) -> Optional[Iterable[InspectorMessage]]:
    """Check that image masks and reference images have the same shape."""
    if plane_segmentation.reference_images and "image_mask" in plane_segmentation.colnames:
        mask_shape = plane_segmentation["image_mask"].shape[1:]
        for ref_image in plane_segmentation.reference_images:
            if mask_shape != ref_image.data.shape[1:]:
                yield InspectorMessage(
                    f"image_mask of shape {mask_shape} does not match reference image {ref_image.name} with shape"
                    f" {ref_image.data.shape[1:]}."
                )

    return None


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImagingPlane)
def check_imaging_plane_location_allen_ccf(imaging_plane: ImagingPlane) -> Optional[InspectorMessage]:
    """
    Check that the ImagingPlane location is a term in the Allen Mouse Brain CCF ontology.

    Only applies when the subject species is mouse.

    Best Practice: :ref:`best_practice_ophys_location`
    """
    nwbfile = imaging_plane.get_ancestor("NWBFile")
    if nwbfile is None or nwbfile.subject is None:
        return None
    species = nwbfile.subject.species
    if species not in MOUSE_SPECIES_VALUES:
        return None

    location = imaging_plane.location
    if location is None:
        return None

    valid_terms = get_allen_ccf_location_terms()
    if location not in valid_terms:
        return InspectorMessage(
            message=(
                f"ImagingPlane location '{location}' is not a term in the Allen Mouse Brain CCF ontology. "
                "Please use either the full name or abbreviation from the Allen Mouse Brain Atlas "
                "(e.g., 'Primary visual area' or 'VISp'). This check can be ignored if Allen CCF "
                "terms do not meet your needs."
            )
        )

    return None


def _declares_depth(image_series: ImageSeries, imaging_plane: ImagingPlane) -> bool:
    """Return True when the file states somewhere that the series has a depth axis."""
    for declaration in (image_series.dimension, imaging_plane.grid_spacing, imaging_plane.origin_coords):
        if declaration is not None and len(declaration) == 3:
            return True
    return False


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=ImageSeries)
def check_photon_series_undeclared_depth(image_series: ImageSeries) -> Optional[InspectorMessage]:
    """
    Check that a photon series with a depth axis of length one is either planar or a described volume.

    Readers tell a plane from a volume by the number of axes, so a trailing axis of length one turns a
    planar recording into a one-plane volume. That axis is usually a channel or plane axis left in place
    after splitting a recording into one series per channel. A single plane should be stored with three
    axes, and a real one-plane volume should give the spacing or position of its planes through a
    three-component ``grid_spacing`` or ``origin_coords`` on the imaging plane.

    Best Practice: :ref:`best_practice_photon_series_depth_axis`
    """
    imaging_plane = getattr(image_series, "imaging_plane", None)
    if imaging_plane is None:  # a plain ImageSeries has no imaging plane and no depth semantics
        return None

    data_shape = get_data_shape(image_series.data, strict_no_data_load=True)
    if data_shape is None or len(data_shape) != 4 or data_shape[3] != 1:
        return None

    if _describes_depth(imaging_plane=imaging_plane):
        return None

    return InspectorMessage(
        message=(
            f"The data is four-dimensional with a depth axis of length 1, but the imaging plane "
            f"('{imaging_plane.name}') does not describe the depth axis. If the recording is a single plane, "
            "store the data as (time, width, height). If it is a one-plane volume, set a three-component "
            "'grid_spacing' or 'origin_coords' on the imaging plane."
        )
    )
