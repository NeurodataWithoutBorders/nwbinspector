"""Authors: Cody Baker and Ben Dichter."""
import numpy as np

import pynwb

from nwbinspector import (
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
)


def test_check_regular_timestamps():
    assert check_regular_timestamps(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
    ) == dict(
        severity="LOW_SEVERITY",
        message=(
            "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 and rate=2.0 "
            "instead of timestamps."
        ),
        importance="BEST_PRACTICE_VIOLATION",
        check_function_name="check_regular_timestamps",
        object_type="TimeSeries",
        object_name="test_time_series",
    )


def test_check_data_orientation():
    assert check_data_orientation(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=(2, 100)),
            rate=1.0,
        )
    ) == dict(
        severity=None,
        message=(
            "Data may be in the wrong orientation. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer. "
        ),
        importance="CRITICAL_IMPORTANCE",
        check_function_name="check_data_orientation",
        object_type="TimeSeries",
        object_name="test_time_series",
    )


def test_check_timestamps():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=4),
            timestamps=[1.0, 2.0, 3.0],
        )
    ) == dict(
        severity=None,
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance="CRITICAL_IMPORTANCE",
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
    )


def test_check_timestamps_empty_data():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[], timestamps=[1.0, 2.0, 3.0])
    ) == dict(
        severity=None,
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance="CRITICAL_IMPORTANCE",
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
    )


def test_check_timestamps_empty_timestamps():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(name="test_time_series", unit="test_units", data=np.zeros(shape=4), timestamps=[])
    ) == dict(
        severity=None,
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance="CRITICAL_IMPORTANCE",
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
    )
