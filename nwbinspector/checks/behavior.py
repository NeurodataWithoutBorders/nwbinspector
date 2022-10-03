"""Checks for types belonging to the pynwb.behavior module."""
import numpy as np
from pynwb.behavior import SpatialSeries, CompassDirection

from ..register_checks import register_check, Importance, InspectorMessage


@register_check(importance=Importance.CRITICAL, neurodata_type=SpatialSeries)
def check_spatial_series_dims(spatial_series: SpatialSeries):
    """Check if a SpatialSeries has the correct dimensions."""
    if len(spatial_series.data.shape) > 1 and spatial_series.data.shape[1] > 3:
        return InspectorMessage(
            message="SpatialSeries should have 1 column (x), 2 columns (x, y), or 3 columns (x, y, z)."
        )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=CompassDirection)
def check_compass_direction_unit(compass_direction: CompassDirection):
    for spatial_series in compass_direction.spatial_series.values():
        if spatial_series.unit not in ("degrees", "radians"):
            yield InspectorMessage(
                message=f"SpatialSeries objects inside a CompassDirection object should be angular and should have a "
                f"unit of 'degrees' or 'radians', but '{spatial_series.name}' has units '{spatial_series.unit}'."
            )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=SpatialSeries)
def check_spatial_series_radians_magnitude(spatial_series: SpatialSeries, nelems: int = 200):
    if spatial_series.unit in ("radian", "radians"):
        data = spatial_series.data[:nelems]
        if np.any(data > (2 * np.pi)) or np.any(data < (-2 * np.pi)):
            return InspectorMessage(
                message="SpatialSeries with units of radians must have values between -2pi and 2pi."
            )


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=SpatialSeries)
def check_spatial_series_degrees_magnitude(spatial_series: SpatialSeries, nelems: int = 200):
    if spatial_series.unit in ("degree", "degrees"):
        data = spatial_series.data[:nelems]
        if np.any(data > 360) or np.any(data < -360):
            return InspectorMessage(
                message="SpatialSeries with units of degrees must have values between -360 and 360."
            )
