import h5py
import numpy as np
import pynwb

from nwbinspector import Importance, InspectorMessage
from nwbinspector.checks import (
    check_data_orientation,
    check_missing_unit,
    check_rate_is_not_zero,
    check_rate_is_positive,
    check_rate_not_below_threshold,
    check_regular_timestamps,
    check_resolution,
    check_time_series_duration,
    check_timestamp_of_the_first_sample_is_not_negative,
    check_timestamps_ascending,
    check_timestamps_match_first_dimension,
    check_timestamps_without_nans,
)
from nwbinspector.testing import check_streaming_tests_enabled, make_minimal_nwbfile

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
            "TimeSeries appears to have a constant sampling rate. Consider specifying starting_time=1.2 and rate=0.5 "
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


def test_check_data_orientation_unbounded_maxshape(tmp_path):
    filepath = tmp_path / "test.nwb"
    with h5py.File(filepath, "w") as file:
        data = file.create_dataset(
            "data",
            data=np.ones((10, 3)),
            maxshape=(None, 3),
        )

        time_series = pynwb.TimeSeries(
            name="test_time_series",
            unit="test_units",
            data=data,
            rate=1.0,
        )

        assert check_data_orientation(time_series) is None


def test_check_timestamps_match_first_dimension_good():
    assert (
        check_timestamps_match_first_dimension(
            time_series=pynwb.TimeSeries(
                name="test_time_series",
                unit="test_units",
                data=np.empty(shape=4),
                timestamps=[1.0, 2.0, 3.0, 4.0],
            )
        )
        is None
    )


def test_check_timestamps_match_first_dimension_special_skip(tmp_path):
    """
    Very special skip condition for a certain older practice for indexing repeated Images.

    The use of an ImageSeries for this is discouraged, with preference to use a stack of unordered Images instead.
    """
    nwbfile_path = tmp_path / "test_check_timestamps_match_first_dimension_special_skip.nwb"

    nwbfile = make_minimal_nwbfile()
    num_images = 5
    image_width = 10
    image_height = 15
    num_channels = 3
    dtype = "uint8"

    # Use __new__ and in_construct_mode=True to bypass the check in pynwb for data.shape[0] == len(timestamps)
    image_series = pynwb.image.ImageSeries.__new__(pynwb.image.ImageSeries, in_construct_mode=True)
    image_series.__init__(
        name="ImageSeries",
        unit="N/A",
        data=np.empty(shape=(num_images, image_width, image_height, num_channels), dtype=dtype),
        timestamps=[],
    )

    # Use __new__ and in_construct_mode=True to bypass the check in pynwb for deprecated indexed_timeseries
    index_series = pynwb.image.IndexSeries.__new__(pynwb.image.IndexSeries, in_construct_mode=True)
    index_series.__init__(
        name="IndexSeries",
        unit="N/A",
        data=np.array([0, 1], dtype=np.uint32),
        indexed_timeseries=image_series,
        timestamps=[0.5, 0.6],
    )
    nwbfile.add_acquisition(image_series)
    nwbfile.add_acquisition(index_series)

    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="w") as io:
        io.write(nwbfile)

    with pynwb.NWBHDF5IO(path=nwbfile_path, mode="r") as io:
        nwbfile_out = io.read()
        image_series_out = nwbfile_out.acquisition["ImageSeries"]

        assert check_timestamps_match_first_dimension(time_series=image_series_out) is None


def test_check_timestamps_match_first_dimension_bad():
    # Use __new__ and in_construct_mode=True to bypass the check in pynwb for data.shape[0] == len(timestamps)
    time_series = pynwb.TimeSeries.__new__(pynwb.TimeSeries, in_construct_mode=True)
    time_series.__init__(
        name="test_time_series",
        unit="test_units",
        data=np.empty(shape=4),
        timestamps=[1.0, 2.0, 3.0],
    )
    assert check_timestamps_match_first_dimension(time_series=time_series) == InspectorMessage(
        message="The length of the first dimension of data (4) does not match the length of timestamps (3).",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_empty_data():
    # Use __new__ and in_construct_mode=True to bypass the check in pynwb for data.shape[0] == len(timestamps)
    time_series = pynwb.TimeSeries.__new__(pynwb.TimeSeries, in_construct_mode=True)
    time_series.__init__(
        name="test_time_series",
        unit="test_units",
        data=[],
        timestamps=[1.0, 2.0, 3.0],
    )
    assert check_timestamps_match_first_dimension(time_series=time_series) == InspectorMessage(
        message="The length of the first dimension of data (0) does not match the length of timestamps (3).",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_empty_timestamps():
    # Use __new__ and in_construct_mode=True to bypass the check in pynwb for data.shape[0] == len(timestamps)
    time_series = pynwb.TimeSeries.__new__(pynwb.TimeSeries, in_construct_mode=True)
    time_series.__init__(
        name="test_time_series",
        unit="test_units",
        data=np.empty(shape=4),
        timestamps=[],
    )
    assert check_timestamps_match_first_dimension(time_series=time_series) == InspectorMessage(
        message="The length of the first dimension of data (4) does not match the length of timestamps (0).",
        importance=Importance.CRITICAL,
        check_function_name="check_timestamps_match_first_dimension",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_rate_is_not_zero_pass():
    time_series = pynwb.TimeSeries(name="test", unit="test_units", data=[1, 2, 3], rate=4.0)
    assert check_rate_is_not_zero(time_series) is None


def test_check_rate_is_not_zero_single_frame_pass():
    time_series = pynwb.TimeSeries(name="test", unit="test_units", data=[1], rate=0.0)
    assert check_rate_is_not_zero(time_series) is None


def test_check_rate_is_not_zero_fail():
    time_series = pynwb.TimeSeries(name="TimeSeriesTest", unit="n.a.", data=[1, 2, 3], rate=0.0)
    assert check_rate_is_not_zero(time_series) == InspectorMessage(
        message="TimeSeriesTest has a sampling rate value of 0.0Hz but the series has more than one frame.",
        importance=Importance.CRITICAL,
        check_function_name="check_rate_is_not_zero",
        object_type="TimeSeries",
        object_name="TimeSeriesTest",
        location="/",
    )


def test_pass_check_timestamps_ascending_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_timestamps_ascending(time_series) is None


def test_pass_check_timestamps_ascending_with_nans_pass():
    time_series = pynwb.TimeSeries(
        name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, np.nan, 3]
    )
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


def test_check_timestamps_ascending_with_nans_fail():
    time_series = pynwb.TimeSeries(
        name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[np.nan, 3, 2]
    )
    assert check_timestamps_ascending(time_series) == InspectorMessage(
        message="test_time_series timestamps are not ascending.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_timestamps_ascending",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamps_without_nans_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[1, 2, 3])
    assert check_timestamps_without_nans(time_series) is None


def test_check_timestamps_without_nans_fail():
    time_series = pynwb.TimeSeries(
        name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[np.nan, 2, 3]
    )
    assert check_timestamps_without_nans(time_series) == InspectorMessage(
        message="test_time_series timestamps contain NaN values.",
        importance=Importance.BEST_PRACTICE_VIOLATION,
        check_function_name="check_timestamps_without_nans",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamp_of_the_first_sample_is_not_negative_with_timestamps_fail():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[-1, 0, 1])
    message = (
        "Timestamps should not be negative. This usually indicates a temporal misalignment of the data. "
        "It is recommended to align the `session_start_time` or `timestamps_reference_time` to be the earliest time value that occurs in the data, and shift all other signals accordingly."
    )
    assert check_timestamp_of_the_first_sample_is_not_negative(time_series) == InspectorMessage(
        message=message,
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_timestamp_of_the_first_sample_is_not_negative",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamp_of_the_first_sample_is_not_negative_with_timestamps_pass():
    time_series = pynwb.TimeSeries(name="test_time_series", unit="test_units", data=[1, 2, 3], timestamps=[0, 1, 2])
    assert check_timestamp_of_the_first_sample_is_not_negative(time_series) is None


def test_check_timestamp_of_the_first_sample_is_not_negative_with_starting_time_fail():

    time_series = pynwb.TimeSeries(
        name="test_time_series", unit="test_units", data=[1, 2, 3], starting_time=-1.0, rate=30.0
    )
    message = (
        "Timestamps should not be negative. This usually indicates a temporal misalignment of the data. "
        "It is recommended to align the `session_start_time` or `timestamps_reference_time` to be the earliest time value that occurs in the data, and shift all other signals accordingly."
    )

    assert check_timestamp_of_the_first_sample_is_not_negative(time_series) == InspectorMessage(
        message=message,
        importance=Importance.BEST_PRACTICE_SUGGESTION,
        check_function_name="check_timestamp_of_the_first_sample_is_not_negative",
        object_type="TimeSeries",
        object_name="test_time_series",
        location="/",
    )


def test_check_timestamp_of_the_first_sample_is_not_negative_with_starting_time_pass():
    time_series = pynwb.TimeSeries(
        name="test_time_series", unit="test_units", data=[1, 2, 3], starting_time=0.0, rate=30.0
    )
    assert check_timestamp_of_the_first_sample_is_not_negative(time_series) is None


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


def test_check_rate_is_positive_pass():
    time_series = pynwb.TimeSeries(name="test", unit="test_units", data=np.array([1, 2, 3]), rate=4.0)
    assert check_rate_is_positive(time_series) is None


def test_check_rate_is_positive_none_pass():
    time_series = pynwb.TimeSeries(
        name="test", unit="test_units", data=np.array([1, 2, 3]), timestamps=np.array([1, 2, 3])
    )
    assert check_rate_is_positive(time_series) is None


# @pytest.mark.skipif(
#    version.parse(pynwb.__version__) >= version.parse("2.5.0"),
#    reason="pynwb >= 2.5.0 prevents setting negative rates"
# )


def test_check_rate_is_positive_fail():
    # Use __new__ and in_construct_mode=True to bypass pynwb validation
    rate = -2.0
    time_series = pynwb.TimeSeries.__new__(pynwb.TimeSeries, in_construct_mode=True)
    time_series.__init__(name="TimeSeriesTest", unit="n.a.", data=np.array([1, 2, 3]), rate=rate)

    assert check_rate_is_positive(time_series) == InspectorMessage(
        message=f"TimeSeriesTest has a negative sampling rate value of {rate}Hz which is not valid.",
        importance=Importance.CRITICAL,
        check_function_name="check_rate_is_positive",
        object_type="TimeSeries",
        object_name="TimeSeriesTest",
        location="/",
    )


def test_check_time_series_duration_pass_short_duration_with_timestamps():
    """Test that a short duration TimeSeries with timestamps passes."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        timestamps=np.linspace(0, 100, 100),  # 100 seconds, much less than 1 year
    )
    assert check_time_series_duration(time_series) is None


def test_check_time_series_duration_pass_short_duration_with_rate():
    """Test that a short duration TimeSeries with rate passes."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=1000),
        starting_time=0.0,
        rate=10.0,  # 1000 samples at 10Hz = 100 seconds
    )
    assert check_time_series_duration(time_series) is None


def test_check_time_series_duration_fail_with_timestamps():
    """Test that a TimeSeries exceeding 1 year duration with timestamps fails."""
    # Create timestamps spanning more than 1 year (31557600 seconds)
    one_year = 31557600.0
    time_series = pynwb.TimeSeries(
        name="long_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        timestamps=np.linspace(0, one_year + 1000, 100),  # Exceeds 1 year
    )
    result = check_time_series_duration(time_series)
    assert result is not None
    assert "long_time_series" in result.message
    assert "exceeds the threshold" in result.message
    assert result.importance == Importance.BEST_PRACTICE_SUGGESTION


def test_check_time_series_duration_fail_with_rate():
    """Test that a TimeSeries exceeding 1 year duration with rate fails."""
    # Create a time series with more than 1 year of data
    one_year = 31557600.0
    rate = 1.0  # 1 Hz
    num_samples = int(one_year + 1000)  # More than 1 year worth of samples
    time_series = pynwb.TimeSeries(
        name="long_time_series",
        unit="test_units",
        data=np.zeros(shape=num_samples),
        starting_time=0.0,
        rate=rate,
    )
    result = check_time_series_duration(time_series)
    assert result is not None
    assert "long_time_series" in result.message
    assert "exceeds the threshold" in result.message
    assert result.importance == Importance.BEST_PRACTICE_SUGGESTION


def test_check_time_series_duration_pass_custom_threshold():
    """Test that the custom duration threshold works correctly."""
    # Create a TimeSeries with 200 seconds duration
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        timestamps=np.linspace(0, 200, 100),
    )
    # Should fail with a threshold of 100 seconds
    result = check_time_series_duration(time_series, duration_threshold=100.0)
    assert result is not None

    # Should pass with a threshold of 300 seconds
    result = check_time_series_duration(time_series, duration_threshold=300.0)
    assert result is None


def test_check_time_series_duration_pass_single_sample():
    """Test that TimeSeries with a single sample passes."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=1),
        timestamps=[0],
    )
    assert check_time_series_duration(time_series) is None


def test_check_time_series_duration_pass_two_samples():
    """Test that TimeSeries with only two samples passes (duration cannot be calculated reliably)."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=2),
        timestamps=[0, 1],
    )
    # Should pass - even though there's a duration, with only 2 samples we skip
    assert check_time_series_duration(time_series) is None


def test_check_rate_not_below_threshold_pass_normal_rate():
    """Test that a normal sampling rate passes."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        starting_time=0.0,
        rate=30.0,  # 30 Hz is a normal rate
    )
    assert check_rate_not_below_threshold(time_series) is None


def test_check_rate_not_below_threshold_fail_very_low_rate():
    """Test that a very low sampling rate fails."""
    low_rate = 0.001  # 0.001 Hz = period of 1000 seconds
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        starting_time=0.0,
        rate=low_rate,
    )
    result = check_rate_not_below_threshold(time_series)
    assert result is not None
    assert "test_time_series" in result.message
    assert f"{low_rate}Hz" in result.message
    assert "period" in result.message
    assert result.importance == Importance.CRITICAL


def test_check_rate_not_below_threshold_fail_period_like_value():
    """Test detection when period was likely used instead of rate."""
    # If someone uses 2.0 thinking it's a 2 second period, the rate should be 0.5 Hz
    period_value = 2.0
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        starting_time=0.0,
        rate=period_value,
    )
    result = check_rate_not_below_threshold(time_series)
    # Should pass with default threshold since 2.0 > 0.01
    assert result is None

    # But should fail with a custom threshold
    result = check_rate_not_below_threshold(time_series, low_rate_threshold=5.0)
    assert result is not None


def test_check_rate_not_below_threshold_pass_custom_threshold():
    """Test that custom threshold works correctly."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        starting_time=0.0,
        rate=0.005,  # Below default threshold of 0.01
    )
    # Should fail with default threshold
    result = check_rate_not_below_threshold(time_series)
    assert result is not None

    # Should pass with lower custom threshold
    result = check_rate_not_below_threshold(time_series, low_rate_threshold=0.001)
    assert result is None


def test_check_rate_not_below_threshold_pass_no_rate():
    """Test that TimeSeries without rate attribute passes."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=100),
        timestamps=np.linspace(0, 100, 100),
    )
    assert check_rate_not_below_threshold(time_series) is None


def test_check_rate_not_below_threshold_pass_zero_rate():
    """Test that zero rate passes (handled by different check)."""
    time_series = pynwb.TimeSeries(
        name="test_time_series",
        unit="test_units",
        data=np.zeros(shape=1),
        starting_time=0.0,
        rate=0.0,
    )
    # Zero rate should pass this check (it's handled by check_rate_is_not_zero)
    assert check_rate_not_below_threshold(time_series) is None
