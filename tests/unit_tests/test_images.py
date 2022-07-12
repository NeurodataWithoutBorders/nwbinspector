import numpy as np

from pynwb.base import Images, ImageReferences
from pynwb.image import GrayscaleImage

from nwbinspector import InspectorMessage, Importance
from nwbinspector.checks.images import check_order_of_images_unique, check_order_of_images_len


def test_check_order_of_images_unique():

    imgs = [GrayscaleImage(name=f"image{i}", data=np.random.randn(10, 10)) for i in range(5)]
    img_refs = ImageReferences(name="order_of_images", data=imgs + [imgs[0]])
    images = Images(name="my_images", images=imgs, order_of_images=img_refs)

    assert check_order_of_images_unique(images) == InspectorMessage(
        message="order_of_images should have unique values.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_order_of_images_unique",
        object_type="Images",
        object_name="my_images",
        location="/",
    )


def test_pass_check_order_of_images_unique():

    imgs = [GrayscaleImage(name=f"image{i}", data=np.random.randn(10, 10)) for i in range(5)]
    img_refs = ImageReferences(name="order_of_images", data=imgs)
    images = Images(name="my_images", images=imgs, order_of_images=img_refs)

    assert check_order_of_images_unique(images) is None


def test_check_order_of_images_len():

    imgs = [GrayscaleImage(name=f"image{i}", data=np.random.randn(10, 10)) for i in range(5)]
    img_refs = ImageReferences(name="order_of_images", data=imgs + [imgs[0]])
    images = Images(name="my_images", images=imgs, order_of_images=img_refs)

    assert check_order_of_images_len(images) == InspectorMessage(
        message=f"Length of order_of_images (6) does not match the number of images (5).",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_order_of_images_len",
        object_type="Images",
        object_name="my_images",
        location="/",
    )


def test_pass_check_order_of_images_len():

    imgs = [GrayscaleImage(name=f"image{i}", data=np.random.randn(10, 10)) for i in range(5)]
    img_refs = ImageReferences(name="order_of_images", data=imgs)
    images = Images(name="my_images", images=imgs, order_of_images=img_refs)

    assert check_order_of_images_len(images) is None