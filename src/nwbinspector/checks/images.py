"""Checks specific to the Images neurodata type."""
from packaging.version import Version

from pynwb.image import IndexSeries

from ..register_checks import register_check, Importance, InspectorMessage
from ..utils import get_package_version

# The Images neurodata type was unavailable prior to PyNWB v.2.1.0
if get_package_version(name="pynwb") >= Version("2.1.0"):
    from pynwb.base import Images

    @register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Images)
    def check_order_of_images_unique(images: Images):
        """Check that all the values in the order_of_images field of an Images object are unique."""
        if images.order_of_images is None:
            return
        if not len(set(images.order_of_images)) == len(images.order_of_images):
            return InspectorMessage(message="order_of_images should have unique values.")

    @register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=Images)
    def check_order_of_images_len(images: Images):
        """Check that all the values in the order_of_images field of an Images object are unique."""
        if images.order_of_images is None:
            return
        if not len(images.order_of_images) == len(images.images):
            return InspectorMessage(
                message=f"Length of order_of_images ({len(images.order_of_images)}) does not match the number of "
                f"images ({len(images.images)})."
            )

    @register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=IndexSeries)
    def check_index_series_points_to_image(index_series: IndexSeries):
        if index_series.indexed_timeseries is not None:
            return InspectorMessage(
                message="Pointing an IndexSeries to a TimeSeries will be deprecated. Please point to an Images "
                "container instead."
            )
