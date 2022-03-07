# """Authors: Cody Baker, Ben Dichter, and Ryan Ly."""
from pynwb.ophys import RoiResponseSeries, PlaneSegmentation

from hdmf.utils import get_data_shape

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.CRITICAL, neurodata_type=RoiResponseSeries)
def check_roi_response_series_dims(roi_response_series: RoiResponseSeries):
    data = roi_response_series.data
    rois = roi_response_series.rois

    data_shape = get_data_shape(data, strict_no_data_load=True)

    if data_shape and len(data_shape) == 2 and data_shape[1] != len(rois.data):
        if data_shape[0] == len(rois.data):
            return InspectorMessage(
                message="The second dimension of data does not match the length of rois, "
                "but instead the first does. Data is oriented incorrectly and should be transposed."
            )
        return InspectorMessage(
            message="The second dimension of data does not match the length of rois. Your data may be transposed."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=RoiResponseSeries)
def check_roi_response_series_link_to_plane_segmentation(roi_response_series: RoiResponseSeries):
    if not isinstance(roi_response_series.rois.table, PlaneSegmentation):
        return InspectorMessage(message="rois field does not point to a PlaneSegmentation table.")


# @nwbinspector_check(severity=2, neurodata_type=pynwb.TimeSeries)
# def check_ophys(nwbfile):
#     opto_sites = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticStimulusSite))
#     opto_series = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticSeries))
#     for site in opto_sites:
#         if not site.description:
#             error_code = "A101"
#             print(
#                 "%s: '%s' %s is missing text for attribute 'description'"
# % (error_code, site.name, type(site).__name__)
#             )
#         if not site.location:
#             error_code = "A101"
#             print("%s: '%s' %s is missing text for attribute 'location'"
# % (error_code, site.name, type(site).__name__))
#     if opto_sites and not opto_series:
#         error_code = "A101"
#         print("%s: OptogeneticStimulusSite object(s) exists without an OptogeneticSeries" % error_code)
