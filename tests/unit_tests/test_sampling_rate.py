"""Unit tests for the sampling-rate and time-scale checks, on small in-memory NWB files."""

from datetime import datetime, timezone

import numpy as np
from pynwb import NWBFile, TimeSeries
from pynwb.ecephys import ElectricalSeries
from pynwb.image import ImageSeries
from pynwb.ophys import (
    ImageSegmentation,
    OpticalChannel,
    RoiResponseSeries,
    TwoPhotonSeries,
)

from nwbinspector import Importance
from nwbinspector.checks import (
    check_equal_length_series_have_equal_duration,
    check_imaging_rate_is_not_sampling_period,
    check_imaging_rate_matches_roi_response_rate,
    check_imaging_rate_matches_series_rate,
    check_rate_in_plausible_range,
    check_rate_is_not_sampling_period,
    check_series_ends_within_session,
    check_starting_time_is_finite,
    check_starting_time_is_not_absolute,
    check_timestamps_time_scale,
)
from nwbinspector.checks._sampling_rate import _SUMMARY_CACHE

SESSION_START = datetime(2024, 1, 1, 12, tzinfo=timezone.utc)


def make_nwbfile():
    _SUMMARY_CACHE.clear()
    return NWBFile(session_description="test", identifier="test", session_start_time=SESSION_START)


def add_series(nwbfile, name, n, **timing):
    series = TimeSeries(name=name, data=np.zeros(n), unit="a.u.", **timing)
    nwbfile.add_acquisition(series)
    return series


def add_imaging(nwbfile, imaging_rate, **timing):
    device = nwbfile.create_device(name="microscope")
    channel = OpticalChannel(name="green", description="green", emission_lambda=520.0)
    plane = nwbfile.create_imaging_plane(
        name="plane",
        optical_channel=channel,
        description="",
        device=device,
        excitation_lambda=920.0,
        imaging_rate=imaging_rate,
        indicator="GCaMP6f",
        location="V1",
    )
    series = TwoPhotonSeries(
        name="TwoPhotonSeries",
        data=np.zeros((300, 4, 4)),
        imaging_plane=plane,
        unit="n.a.",
        **timing,
    )
    nwbfile.add_acquisition(series)
    return plane, series


def test_period_as_rate_by_session_span():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)  # 3000 s session
    wheel = add_series(nwbfile, "wheel", n=120_000, rate=0.025)  # 40 Hz stored as its period
    message = check_rate_is_not_sampling_period(wheel)
    assert message is not None and message.importance == Importance.CRITICAL
    assert "reciprocal" in message.message


def test_period_as_rate_by_reciprocal_of_related_rate():
    nwbfile = make_nwbfile()
    add_imaging(nwbfile, imaging_rate=30.0, rate=30.0)
    trial = add_series(nwbfile, "trial_trace", n=40, rate=1 / 30.9)
    assert check_rate_is_not_sampling_period(trial) is not None


def test_genuinely_slow_series_passes():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "ephys_like", n=3_000_000, rate=1000.0)  # 3000 s session
    temperature = add_series(nwbfile, "temperature", n=300, rate=0.1)  # 3000 s at 0.1 Hz
    assert check_rate_is_not_sampling_period(temperature) is None


def test_timestamps_in_milliseconds():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)
    video = add_series(nwbfile, "video", n=90_000, timestamps=np.arange(90_000) * 33.3)  # ms
    message = check_timestamps_time_scale(video)
    assert message is not None and "milliseconds" in message.message


def test_timestamps_in_kiloseconds():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)
    photometry = add_series(nwbfile, "photometry", n=36_000_000, timestamps=np.arange(36_000_000) / 12e6)
    assert check_timestamps_time_scale(photometry) is not None
    assert check_rate_in_plausible_range(photometry) is not None


def test_short_event_series_is_not_flagged():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)
    events = add_series(
        nwbfile,
        "events",
        n=20,
        timestamps=np.sort(np.random.default_rng(0).uniform(0, 3, 20)),
    )
    assert check_timestamps_time_scale(events) is None


def test_ephys_rate_of_one_hz():
    nwbfile = make_nwbfile()
    device = nwbfile.create_device(name="probe")
    group = nwbfile.create_electrode_group(name="shank", description="", location="CA1", device=device)
    nwbfile.add_electrode(group=group, location="CA1")
    region = nwbfile.create_electrode_table_region(region=[0], description="all")
    series = ElectricalSeries(name="ElectricalSeries", data=np.zeros((1000, 1)), electrodes=region, rate=1.0)
    nwbfile.add_acquisition(series)
    assert check_rate_in_plausible_range(series) is not None


def test_imaging_rate_mismatch_and_reciprocal():
    nwbfile = make_nwbfile()
    plane, series = add_imaging(nwbfile, imaging_rate=30.0, timestamps=np.arange(300) / 4.5)
    assert check_imaging_rate_matches_series_rate(series) is not None
    nwbfile = make_nwbfile()
    plane, series = add_imaging(nwbfile, imaging_rate=0.83, rate=1.2048)
    assert check_imaging_rate_is_not_sampling_period(plane) is not None
    nwbfile = make_nwbfile()
    plane, series = add_imaging(nwbfile, imaging_rate=30.0, rate=30.0)
    assert check_imaging_rate_matches_series_rate(series) is None


def test_equal_length_series_disagree():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "photometry", n=1000, rate=9.0)
    add_series(nwbfile, "behavior", n=1000, timestamps=np.arange(1000) / 18.0)
    messages = check_equal_length_series_have_equal_duration(nwbfile)
    assert messages is not None and len(messages) == 1


def test_starting_time_unix_and_nan():
    nwbfile = make_nwbfile()
    absolute = add_series(
        nwbfile,
        "absolute",
        n=100,
        rate=6.0,
        starting_time=SESSION_START.timestamp() + 5,
    )
    assert check_starting_time_is_not_absolute(absolute) is not None
    missing = add_series(nwbfile, "missing", n=100, rate=6.0, starting_time=float("nan"))
    assert check_starting_time_is_finite(missing) is not None
    fine = add_series(nwbfile, "fine", n=100, rate=6.0, starting_time=5.0)
    assert check_starting_time_is_not_absolute(fine) is None and check_starting_time_is_finite(fine) is None


def test_unix_times_allowed_when_reference_is_epoch():
    _SUMMARY_CACHE.clear()
    nwbfile = NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=SESSION_START,
        timestamps_reference_time=datetime(1970, 1, 1, tzinfo=timezone.utc),
    )
    unix = add_series(
        nwbfile,
        "unix",
        n=100,
        timestamps=SESSION_START.timestamp() + np.arange(100) / 30,
    )
    assert check_starting_time_is_not_absolute(unix) is None


def test_frame_indices_as_timestamps():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=36_000, rate=10.0)  # 3600 s session
    frames = add_series(nwbfile, "stimulus_frames", n=1200, timestamps=np.arange(1200) * 90.0)
    message = check_timestamps_time_scale(frames)
    assert message is not None and "indices" in message.message


def test_equal_length_series_in_nanoseconds():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "analog", n=1000, timestamps=np.arange(1000) / 30.0)
    add_series(nwbfile, "sample_count", n=1000, timestamps=np.arange(1000) / 30.0 * 1e9)
    messages = check_equal_length_series_have_equal_duration(nwbfile)
    assert messages is not None and "nanoseconds" in messages[0].message


def test_roi_traces_disagree_with_imaging_rate():
    nwbfile = make_nwbfile()
    device = nwbfile.create_device(name="microscope")
    channel = OpticalChannel(name="green", description="green", emission_lambda=520.0)
    plane = nwbfile.create_imaging_plane(
        name="plane",
        optical_channel=channel,
        description="",
        device=device,
        excitation_lambda=920.0,
        imaging_rate=100.0,
        indicator="GCaMP6f",
        location="V1",
    )
    image_segmentation = ImageSegmentation()
    segmentation = image_segmentation.create_plane_segmentation(
        name="PlaneSegmentation", description="", imaging_plane=plane
    )
    segmentation.add_roi(image_mask=np.ones((4, 4)))
    ophys = nwbfile.create_processing_module(name="ophys", description="")
    ophys.add(image_segmentation)
    region = segmentation.create_roi_table_region(region=[0], description="all")
    traces = RoiResponseSeries(
        name="traces",
        data=np.zeros((1000, 1)),
        rois=region,
        unit="n.a.",
        timestamps=np.arange(1000) / 4.52,
    )
    ophys.add(traces)
    message = check_imaging_rate_matches_roi_response_rate(traces)
    assert message is not None and "4.52" in message.message


def test_irregular_stimulus_blocks_are_not_compared():
    nwbfile = make_nwbfile()
    rng = np.random.default_rng(0)
    block_a = np.sort(np.concatenate([start + np.arange(500) / 30 for start in rng.uniform(0, 3000, 4)]))
    block_b = np.sort(np.concatenate([start + np.arange(500) / 30 for start in rng.uniform(0, 4000, 4)]))
    add_series(nwbfile, "movie_a", n=2000, timestamps=block_a)
    add_series(nwbfile, "movie_b", n=2000, timestamps=block_b)
    assert check_equal_length_series_have_equal_duration(nwbfile) is None


def test_series_running_far_past_session():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)  # 3000 s session
    fiber = add_series(nwbfile, "fiber", n=280_000, rate=1.0)  # 50 Hz data stated as 1 Hz
    message = check_series_ends_within_session(fiber)
    assert message is not None and "3.2 days" in message.message
    slow = add_series(nwbfile, "temperature", n=300, rate=0.1)
    assert check_series_ends_within_session(slow) is None


def test_timestamps_in_nanoseconds():
    nwbfile = make_nwbfile()
    add_series(nwbfile, "reference", n=30_000, rate=10.0)
    counter = add_series(nwbfile, "sample_count", n=3000, timestamps=np.arange(3000) * 1e9)
    message = check_timestamps_time_scale(counter)
    assert message is not None and "nanoseconds" in message.message


def test_short_ephys_stub_is_not_the_reference():
    nwbfile = make_nwbfile()
    device = nwbfile.create_device(name="probe")
    group = nwbfile.create_electrode_group(name="shank", description="", location="CA1", device=device)
    nwbfile.add_electrode(group=group, location="CA1")
    region = nwbfile.create_electrode_table_region(region=[0], description="all")
    stub = ElectricalSeries(name="ElectricalSeries", data=np.zeros((100, 1)), electrodes=region, rate=30_000.0)
    nwbfile.add_acquisition(stub)
    video = ImageSeries(
        name="video",
        external_file=["video.mp4"],
        starting_frame=[0],
        format="external",
        unit="n.a.",
        timestamps=np.arange(250_000) / 25.0,
    )  # 10000 s, frames in an external file
    nwbfile.add_acquisition(video)
    tracking = add_series(nwbfile, "tracking", n=7201, rate=1.0, starting_time=2871.0)
    assert check_series_ends_within_session(tracking) is None
