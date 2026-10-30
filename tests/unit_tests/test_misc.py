import warnings

import numpy as np
from pynwb.misc import DecompositionSeries
from pynwb.testing.mock.ecephys import mock_ElectricalSeries

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_decomposition_series_source_timeseries,
    check_decomposition_series_unit,
)


def _make_decomposition_series(metric="phase", unit="radians", source_timeseries=None):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return DecompositionSeries(
            name="test",
            data=np.ones((10, 2, 3)),
            metric=metric,
            unit=unit,
            rate=1.0,
            source_timeseries=source_timeseries,
        )


def test_pass_decomposition_series_unit_phase_radians():
    ds = _make_decomposition_series(metric="phase", unit="radians")
    assert check_decomposition_series_unit(ds) is None


def test_pass_decomposition_series_unit_phase_degrees():
    ds = _make_decomposition_series(metric="phase", unit="degrees")
    assert check_decomposition_series_unit(ds) is None


def test_fail_decomposition_series_unit_phase_wrong():
    ds = _make_decomposition_series(metric="phase", unit="volts")
    result = check_decomposition_series_unit(ds)
    assert result == InspectorMessage(
        message=(
            "DecompositionSeries with metric 'phase' should have unit 'radians' or 'degrees', " "but has unit 'volts'."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_decomposition_series_unit",
        object_type="DecompositionSeries",
        object_name="test",
        location="/",
    )


def test_fail_decomposition_series_unit_no_unit():
    ds = _make_decomposition_series(metric="amplitude", unit="no unit")
    result = check_decomposition_series_unit(ds)
    assert result is not None
    assert "no unit" in result.message
    assert "amplitude" in result.message


def test_decomposition_series_unit_empty_string_deferred_to_missing_unit():
    # A truly empty unit is left to the general `check_missing_unit` so the field is not flagged twice.
    ds = _make_decomposition_series(metric="power", unit="")
    assert check_decomposition_series_unit(ds) is None


def test_fail_decomposition_series_unit_phase_case_insensitive_metric():
    ds = _make_decomposition_series(metric="Phase", unit="volts")
    result = check_decomposition_series_unit(ds)
    assert result == InspectorMessage(
        message=(
            "DecompositionSeries with metric 'phase' should have unit 'radians' or 'degrees', " "but has unit 'volts'."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_decomposition_series_unit",
        object_type="DecompositionSeries",
        object_name="test",
        location="/",
    )


def test_pass_decomposition_series_unit_amplitude_matches_source():
    source = mock_ElectricalSeries()
    ds = _make_decomposition_series(metric="amplitude", unit="volts", source_timeseries=source)
    assert check_decomposition_series_unit(ds) is None


def test_fail_decomposition_series_unit_amplitude_mismatch():
    source = mock_ElectricalSeries()
    ds = _make_decomposition_series(metric="amplitude", unit="watts", source_timeseries=source)
    result = check_decomposition_series_unit(ds)
    assert result == InspectorMessage(
        message=(
            "DecompositionSeries with metric 'amplitude' should have the same unit as the source "
            "TimeSeries ('volts'), but has unit 'watts'."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_decomposition_series_unit",
        object_type="DecompositionSeries",
        object_name="test",
        location="/",
    )


def test_pass_decomposition_series_source_set():
    source = mock_ElectricalSeries()
    ds = _make_decomposition_series(source_timeseries=source)
    assert check_decomposition_series_source_timeseries(ds) is None


def test_fail_decomposition_series_source_not_set():
    ds = _make_decomposition_series()
    result = check_decomposition_series_source_timeseries(ds)
    assert result == InspectorMessage(
        message=(
            "DecompositionSeries does not have a source_timeseries linked. "
            "Setting source_timeseries provides provenance about which signal was decomposed "
            "and enables validation of the unit field."
        ),
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_decomposition_series_source_timeseries",
        object_type="DecompositionSeries",
        object_name="test",
        location="/",
    )
