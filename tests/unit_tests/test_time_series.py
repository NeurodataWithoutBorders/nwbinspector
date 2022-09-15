import numpy as np
import pynwb
import pytest
from packaging import version

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
from nwbinspector.testing import check_streaming_tests_enabled
from nwbinspector.utils import get_package_version, robust_s3_read

STREAMING_TESTS_ENABLED, DISABLED_STREAMING_TESTS_REASON = check_streaming_tests_enabled()


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


def test_pass_check_timestamps_ascending_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_timestamps_ascending(time_series) is None


def test_check_timestamps_ascending_fail():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 3, 2])
    assert check_timestamps_ascending(time_series) == InspectorMessage(
        message="test_time_series timestamps are not ascending.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_timestamps_ascending",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


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
    assert check_resolution(time_series) is None


def test_check_unknown_resolution_pass():
    for valid_unknown in [-1.0, np.nan]:
        time_series = pynwb.TimeSeries(name="test", unit="test", data=[1], timestamps=[1], resolution=valid_unknown)
        assert check_resolution(time_series) is None


@pytest.mark.skipif(
    not STREAMING_TESTS_ENABLED or get_package_version("hdmf") >= version.parse("3.3.1"),
    reason=f"{DISABLED_STREAMING_TESTS_REASON or ''}. Also needs 'hdmf<3.3.1'.",
)
def test_check_none_matnwb_resolution_pass():
    """
    Special test on the original problematic file found at

    https://dandiarchive.org/dandiset/000065/draft/files?location=sub-Kibbles%2F

    produced with MatNWB, when read with PyNWB~=2.0.1 and HDMF<=3.2.1 contains a resolution value of None.
    """
    with pynwb.NWBHDF5IO(
        path="https://dandiarchive.s3.amazonaws.com/blobs/da5/107/da510761-653e-4b81-a330-9cdae4838180",
        mode="r",
        load_namespaces=True,
        driver="ros3",
    ) as io:
        nwbfile = robust_s3_read(command=io.read)
        time_series = robust_s3_read(
            command=nwbfile.processing["video_files"]["video"].time_series.get,
            command_args=["20170203_KIB_01_s1.1.h264"],
        )
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
