from pynwb.behavior import SpatialSeries
import numpy as np

from nwbinspector.checks.behavior import check_spatial_series_dims


def test_check_spatial_series_dims():

    spatial_series = SpatialSeries(
        name="SpatialSeries",
        description="description",
        data=np.ones((10, 4)),
        rate=3.0,
        reference_frame="reference_frame",
    )

    assert (
        check_spatial_series_dims(spatial_series).message == "SpatialSeries should have either 2 columns (x,"
        "y) or 3 columns (x,y,z)."
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