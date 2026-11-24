"""Tests for check_ragged_times_repeated. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from hdmf.common import DynamicTable
from pynwb import NWBHDF5IO, NWBFile

from nwbinspector import Importance
from nwbinspector.checks import check_ragged_times_repeated


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


def test_ragged_times_repeated(roundtrip):
    rng = np.random.default_rng(9)
    nwbfile = _new_nwbfile()
    events = DynamicTable(name="annotated_events", description="events")
    events.add_column(name="event_times", description="times", index=True)
    events.add_column(name="label", description="label")
    base = np.sort(rng.uniform(0, 100, 40))
    events.add_row(event_times=np.sort(np.concatenate([base] * 5)), label="cue")
    events.add_row(event_times=np.sort(rng.uniform(0, 100, 40)), label="reward")
    nwbfile.add_acquisition(events)
    read_nwbfile = roundtrip(nwbfile)
    messages = _messages(check_ragged_times_repeated(read_nwbfile.acquisition["annotated_events"]))
    assert len(messages) == 1
    assert messages[0].importance == Importance.CRITICAL
    assert "160 of 200 times are repeats" in messages[0].message


def test_ragged_times_repeated_pass_for_millisecond_times(roundtrip):
    rng = np.random.default_rng(10)
    nwbfile = _new_nwbfile()
    events = DynamicTable(name="annotated_events", description="events")
    events.add_column(name="event_times", description="times", index=True)
    times = np.sort(np.round(rng.uniform(0, 1, 500), 2))  # 10 ms resolution, so many times coincide
    events.add_row(event_times=times)
    nwbfile.add_acquisition(events)
    read_nwbfile = roundtrip(nwbfile)
    assert check_ragged_times_repeated(read_nwbfile.acquisition["annotated_events"]) is None


def test_ragged_times_repeated_skips_spike_times(roundtrip):
    nwbfile = _new_nwbfile()
    nwbfile.add_unit(spike_times=np.repeat(np.linspace(0.0001, 1.2345, 200), 2))
    assert check_ragged_times_repeated(roundtrip(nwbfile).units) is None
