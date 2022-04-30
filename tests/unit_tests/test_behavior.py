from pynwb.behavior import SpatialSeries, CompassDirection
import numpy as np

from nwbinspector import InspectorMessage, Importance
from nwbinspector.checks.behavior import check_compass_direction_unit, check_spatial_series_dims


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


def test_trigger_check_compass_direction_unit():
    obj = CompassDirection(
        spatial_series=SpatialSeries(
            name="SpatialSeries",
            description="description",
            data=np.ones((10,)),
            rate=3.0,
            reference_frame="reference_frame",
        )
    )

    assert (
        check_compass_direction_unit(obj)[0].message == f"SpatialSeries objects inside a CompassDirection object "
        f"should be angular and should have a unit of 'degrees' or 'radians', but 'SpatialSeries' has units 'meters'."
    )


def test_pass_check_compass_direction_unit():
    for unit in ("radians", "degrees"):
        obj = CompassDirection(
            spatial_series=SpatialSeries(
                name="SpatialSeries",
                description="description",
                data=np.ones((10,)),
                rate=3.0,
                reference_frame="reference_frame",
                unit=unit,
            )
        )

        assert check_compass_direction_unit(obj) is None
