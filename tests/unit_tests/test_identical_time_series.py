"""Tests for check_identical_time_series and check_redundant_time_series_copies. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from pynwb import NWBHDF5IO, NWBFile, TimeSeries

from nwbinspector import Importance
from nwbinspector.checks import (
    check_identical_time_series,
    check_redundant_time_series_copies,
)
from nwbinspector.utils import _comparison


def _new_nwbfile() -> NWBFile:
    return NWBFile(
        session_description="test", identifier="id", session_start_time=datetime(2026, 1, 1, tzinfo=timezone.utc)
    )


@pytest.fixture
def roundtrip(tmp_path):
    """Write an NWBFile to disk and return it read back, closing the file afterwards."""
    ios = []

    def _roundtrip(nwbfile: NWBFile) -> NWBFile:
        path = tmp_path / f"test_{len(ios)}.nwb"
        with NWBHDF5IO(path, "w") as io:
            io.write(nwbfile)
        io = NWBHDF5IO(path, "r")
        ios.append(io)
        return io.read()

    yield _roundtrip
    for io in ios:
        io.close()


def _messages(result):
    if result is None:
        return []
    return [result] if not isinstance(result, list) else [m for m in result if m is not None]


def test_identical_time_series(roundtrip):
    rng = np.random.default_rng(3)
    nwbfile = _new_nwbfile()
    raw = rng.normal(size=(1000, 4)).astype("float32")
    nwbfile.add_acquisition(TimeSeries(name="raw", data=raw, unit="V", rate=1000.0))
    module = nwbfile.create_processing_module(name="ecephys", description="ecephys")
    module.add(TimeSeries(name="lfp", data=raw.copy(), unit="V", rate=1000.0))  # processed series equal to raw
    nwbfile.add_acquisition(TimeSeries(name="zeros1", data=np.zeros(500), unit="V", rate=10.0))
    nwbfile.add_acquisition(TimeSeries(name="zeros2", data=np.zeros(500), unit="V", rate=10.0))
    timestamps = np.sort(rng.uniform(0, 100, 200))
    nwbfile.add_acquisition(TimeSeries(name="lick", data=np.ones(200), unit="n.a.", timestamps=timestamps))
    nwbfile.add_acquisition(TimeSeries(name="reward", data=np.ones(200), unit="n.a.", timestamps=timestamps.copy()))
    nwbfile.add_acquisition(
        TimeSeries(name="other_lick", data=np.ones(200), unit="n.a.", timestamps=np.sort(rng.uniform(0, 100, 200)))
    )
    read_nwbfile = roundtrip(nwbfile)

    messages = _messages(check_identical_time_series(read_nwbfile))
    assert len(messages) == 2
    assert all(m.importance == Importance.CRITICAL for m in messages)
    text = " ".join(m.message for m in messages)
    assert "raw" in text and "ecephys/lfp" in text
    assert "lick" in text and "reward" in text and "zeros" not in text
    assert check_redundant_time_series_copies(read_nwbfile) is None


def test_redundant_time_series_copies(roundtrip):
    rng = np.random.default_rng(4)
    nwbfile = _new_nwbfile()
    module = nwbfile.create_processing_module(name="ecephys", description="ecephys")
    phase = rng.uniform(-np.pi, np.pi, size=(2000, 2))
    module.add(TimeSeries(name="up_phase", data=phase, unit="radians", rate=1250.0))
    module.add(TimeSeries(name="spindle_phase", data=phase.copy(), unit="radians", rate=1250.0))
    read_nwbfile = roundtrip(nwbfile)

    assert check_identical_time_series(read_nwbfile) is None
    messages = _messages(check_redundant_time_series_copies(read_nwbfile))
    assert len(messages) == 1
    assert messages[0].importance == Importance.BEST_PRACTICE_VIOLATION


def test_identical_time_series_pass_for_link(roundtrip):
    rng = np.random.default_rng(5)
    nwbfile = _new_nwbfile()
    series = TimeSeries(name="a", data=rng.normal(size=500), unit="V", rate=10.0)
    nwbfile.add_acquisition(series)
    nwbfile.add_acquisition(TimeSeries(name="b", data=series, unit="V", rate=10.0))
    read_nwbfile = roundtrip(nwbfile)
    assert check_identical_time_series(read_nwbfile) is None
    assert check_redundant_time_series_copies(read_nwbfile) is None


def test_identical_time_series_sampled(roundtrip, monkeypatch):
    monkeypatch.setattr(_comparison, "FULL_READ_BYTES", 64 * 1024)
    rng = np.random.default_rng(12)
    nwbfile = _new_nwbfile()
    data = rng.normal(size=(50_000, 2))
    nwbfile.add_acquisition(TimeSeries(name="raw", data=data, unit="V", rate=1000.0))
    module = nwbfile.create_processing_module(name="ecephys", description="ecephys")
    module.add(TimeSeries(name="filtered", data=data.copy(), unit="V", rate=1000.0))
    messages = _messages(check_identical_time_series(roundtrip(nwbfile)))
    assert len(messages) == 1
    assert "sampled blocks" in messages[0].message
