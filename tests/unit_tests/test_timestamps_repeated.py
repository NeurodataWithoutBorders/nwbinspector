"""Tests for check_timestamps_repeated. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from pynwb import NWBHDF5IO, NWBFile, TimeSeries

from nwbinspector import Importance
from nwbinspector.checks import check_timestamps_repeated


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


def test_timestamps_repeated(roundtrip):
    rng = np.random.default_rng(11)
    nwbfile = _new_nwbfile()
    timestamps = np.sort(rng.uniform(0, 100, 300))
    nwbfile.add_acquisition(
        TimeSeries(name="doubled", data=np.arange(600), unit="n.a.", timestamps=np.sort(np.r_[timestamps, timestamps]))
    )
    nwbfile.add_acquisition(TimeSeries(name="clean", data=np.arange(300), unit="n.a.", timestamps=timestamps))
    read_nwbfile = roundtrip(nwbfile)
    message = check_timestamps_repeated(read_nwbfile.acquisition["doubled"])
    assert message is not None
    assert message.importance == Importance.CRITICAL
    assert "300 of 600 timestamps" in message.message
    assert check_timestamps_repeated(read_nwbfile.acquisition["clean"]) is None


def test_timestamps_repeated_pass_for_millisecond_timestamps(roundtrip):
    nwbfile = _new_nwbfile()
    timestamps = np.sort(np.round(np.random.default_rng(15).uniform(0, 1, 500), 2))
    nwbfile.add_acquisition(TimeSeries(name="coarse", data=np.arange(500), unit="n.a.", timestamps=timestamps))
    assert check_timestamps_repeated(roundtrip(nwbfile).acquisition["coarse"]) is None
