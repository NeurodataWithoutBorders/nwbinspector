from pynwb.behavior import SpatialSeries
import numpy as np

from nwbinspector import InspectorMessage, Importance, check_spatial_series_dims


def test_check_spatial_series_dims():

    spatial_series = SpatialSeries(
        name="SpatialSeries",
        description="description",
        data=np.ones((10, 4)),
        rate=3.0,
        reference_frame="reference_frame",
    )
    assert check_spatial_series_dims(spatial_series) == InspectorMessage(
        message="SpatialSeries should have 1 column (x), 2 columns (x, y), or 3 columns (x, y, z).",
        importance=Importance.CRITICAL,
        check_function_name="check_spatial_series_dims",
        object_type="SpatialSeries",
        object_name="SpatialSeries",
        location="/",
    )


def test_pass_check_spatial_series_dims():

    spatial_series = SpatialSeries(
        name="SpatialSeries",
        description="description",
        data=np.ones((10, 3)),
        rate=3.0,
        reference_frame="reference_frame",
    )

    assert check_spatial_series_dims(spatial_series) is None


def test_pass_check_spatial_series_dims_1d():

    spatial_series = SpatialSeries(
        name="SpatialSeries",
        description="description",
        data=np.ones((10,)),
        rate=3.0,
        reference_frame="reference_frame",
    )

    assert check_spatial_series_dims(spatial_series) is None
