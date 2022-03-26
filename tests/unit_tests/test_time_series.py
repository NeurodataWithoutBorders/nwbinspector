import numpy as np

import pynwb

from nwbinspector import (
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
    check_timestamps_ascending,
    check_time_series_data_is_not_none,
    Importance,
)
from nwbinspector import InspectorMessage


def test_check_regular_timestamps():
    assert check_regular_timestamps(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=3),
            timestamps=[1.2, 3.2, 5.2],
        )
    ) == InspectorMessage(
        message=(
            "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 and rate=2.0 "
            "instead of timestamps."
        ),
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_regular_timestamps",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_data_orientation():
    assert check_data_orientation(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=(2, 100)),
            rate=1.0,
        )
    ) == InspectorMessage(
        message=(
            "Data may be in the wrong orientation. "
            "Time should be in the first dimension, and is usually the longest dimension. "
            "Here, another dimension is longer."
        ),
        importance=Importance.CRITICAL,
        check_function_name="check_data_orientation",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=np.zeros(shape=4),
            timestamps=[1.0, 2.0, 3.0],
        )
    ) == InspectorMessage(
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_empty_data():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[], timestamps=[1.0, 2.0, 3.0])
    ) == InspectorMessage(
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_empty_timestamps():
    assert check_timestamps_match_first_dimension(
        time_series=pynwb.TimeSeries(name="test_time_series", unit="test_units", data=np.zeros(shape=4), timestamps=[])
    ) == InspectorMessage(
        message="The length of the first dimension of data does not match the length of timestamps.",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_ascending():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 3, 2])
    assert check_timestamps_ascending(time_series) == InspectorMessage(
        message="test_time_series timestamps are not ascending.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_timestamps_ascending",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_pass_check_timestamps_ascending():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_timestamps_ascending(time_series) is None


def test_check_time_series_data_is_not_none_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_time_series_data_is_not_none(time_series=time_series) is None


def test_check_time_series_data_is_not_none_image_series_pass():
    time_series = pynwb.image.ImageSeries(name="test_time_series", unit="test_units", rate=1.0, external_file=["1"])
    assert check_time_series_data_is_not_none(time_series=time_series) is None


def test_check_time_series_data_is_not_none_fail():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[None], timestamps=[1, 2, 3])
    assert check_time_series_data_is_not_none(time_series=time_series) == InspectorMessage(
        message="Data values in a TimeSeries cannot be None.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_time_series_data_is_not_none",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )
