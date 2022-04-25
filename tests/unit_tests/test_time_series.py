import numpy as np

import pynwb
import pytest

from nwbinspector import (
    InspectorMessage,
    Importance,
    check_regular_timestamps,
    check_data_orientation,
    check_timestamps_match_first_dimension,
    check_timestamps_ascending,
    check_missing_unit,
    check_resolution,
)

try:
    with pynwb.NWBHDF5IO(
        path="https://dandiarchive.s3.amazonaws.com/blobs/da5/107/da510761-653e-4b81-a330-9cdae4838180",
        mode="r",
        load_namespaces=True,
        driver="ros3",
    ) as io:
        nwbfile = io.read()
    HAVE_ROS3 = True
except ValueError:  # ValueError: h5py was built without ROS3 support, can't use ros3 driver
    HAVE_ROS3 = False


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


def test_pass_check_regular_timestamps():
    """Should pass because there are only two timestamps"""
    assert (
        check_regular_timestamps(
            time_series=pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=[0, 0],
                timestamps=[1.2, 3.2],
            )
        )
        is None
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


def test_check_missing_unit_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_missing_unit(time_series) is None


def test_check_missing_unit_fail():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_missing_unit(time_series) == InspectorMessage(
        message="Missing text for attribute 'unit'. Please specify the scientific unit of the 'data'.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_missing_unit",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_positive_resolution_pass():
    time_series = pynwb.TimeSeries(name="test", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3], resolution=3.4)
    assert check_timestamps_ascending(time_series) is None


def test_check_unknown_resolution_pass():
    for valid_unknown in [-1.0, np.nan]:
        time_series = pynwb.TimeSeries(name="test", unit="test", data=[1], timestamps=[1], resolution=valid_unknown)
        assert check_resolution(time_series) is None


@pytest.mark.skipif(not HAVE_ROS3, reason="Needs h5py setup with ROS3.")
def test_check_none_matnwb_resolution_pass():
    with pynwb.NWBHDF5IO(
        path="https://dandiarchive.s3.amazonaws.com/blobs/da5/107/da510761-653e-4b81-a330-9cdae4838180",
        mode="r",
        load_namespaces=True,
        driver="ros3",
    ) as io:
        nwbfile = io.read()
        time_series = nwbfile.processing["video_files"]["video"].time_series["20170203_KIB_01_s1.1.h264"]
        assert check_resolution(time_series) is None


def test_check_resolution_fail():
    time_series = pynwb.TimeSeries(name="test", unit="test", data=[1, 2, 3], timestamps=[1, 2, 3], resolution=-2.0)
    assert check_resolution(time_series) == InspectorMessage(
        message="'resolution' should use -1.0 or NaN for unknown instead of -2.0.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_resolution",
        object_type="TimeSeries",
        object_name="test",
        location="/",
    )
