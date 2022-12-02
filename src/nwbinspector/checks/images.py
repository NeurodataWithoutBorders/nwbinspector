"""Checks specific to the Images neurodata type."""
from pynwb.base import Images

from ..register_checks import register_check, Importance, InspectorMessage


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
