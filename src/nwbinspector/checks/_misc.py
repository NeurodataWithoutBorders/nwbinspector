"""Checks specific to neurodata types in the pynwb.misc module."""

from typing import Optional

from pynwb.misc import DecompositionSeries

from .._registration import Importance, InspectorMessage, register_check


@register_check(importance=Importance.BEST_PRACTICE_VIOLATION, neurodata_type=DecompositionSeries)
def check_decomposition_series_unit(
    decomposition_series: DecompositionSeries,
) -> Optional[InspectorMessage]:
    """
    Check that DecompositionSeries has an appropriate unit for its metric.

    Best Practice: :ref:`best_practice_decomposition_series_unit`
    """
    unit = decomposition_series.unit
    metric = decomposition_series.metric

    if unit in ("no unit", ""):
        return InspectorMessage(
            message=(
                f"DecompositionSeries unit is '{unit}'. "
                f"Please specify the unit appropriate for the metric '{metric}' "
                "(e.g., 'radians' or 'degrees' for phase, or the source signal unit for amplitude)."
            )
        )

    if metric == "phase" and unit not in ("radians", "degrees"):
        return InspectorMessage(
            message=(
                f"DecompositionSeries with metric 'phase' should have unit 'radians' or 'degrees', "
                f"but has unit '{unit}'."
            )
        )

    if metric == "amplitude" and decomposition_series.source_timeseries is not None:
        source_unit = decomposition_series.source_timeseries.unit
        if unit != source_unit:
            return InspectorMessage(
                message=(
                    f"DecompositionSeries with metric 'amplitude' should have the same unit as the source "
                    f"TimeSeries ('{source_unit}'), but has unit '{unit}'."
                )
            )

    return None


@register_check(importance=Importance.BEST_PRACTICE_SUGGESTION, neurodata_type=DecompositionSeries)
def check_decomposition_series_source_timeseries(
    decomposition_series: DecompositionSeries,
) -> Optional[InspectorMessage]:
    """
    Check that DecompositionSeries has a source_timeseries linked.

    Best Practice: :ref:`best_practice_decomposition_series_source`
    """
    if decomposition_series.source_timeseries is None:
        return InspectorMessage(
            message=(
                "DecompositionSeries does not have a source_timeseries linked. "
                "Setting source_timeseries provides provenance about which signal was decomposed "
                "and enables validation of the unit field."
            )
        )

    return None
