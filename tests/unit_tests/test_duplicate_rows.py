"""Tests for check_duplicate_rows. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from hdmf.common import DynamicTable, VectorData
from pynwb import NWBHDF5IO, NWBFile
from pynwb.epoch import TimeIntervals

from nwbinspector import Importance
from nwbinspector.checks import check_duplicate_rows


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


def test_duplicate_rows_events_stored_several_times(roundtrip):
    rng = np.random.default_rng(1)
    nwbfile = _new_nwbfile()
    events = TimeIntervals(name="events", description="events")
    events.add_column(name="label", description="label")
    times = np.sort(rng.uniform(0, 100, 30))
    for _ in range(5):
        for t in times:
            events.add_row(start_time=t, stop_time=t + 0.1, label="cue")
    nwbfile.add_time_intervals(events)
    messages = _messages(check_duplicate_rows(roundtrip(nwbfile).intervals["events"]))
    assert len(messages) == 1
    assert messages[0].importance == Importance.CRITICAL
    assert "120 of 150 rows repeat another row" in messages[0].message


def test_duplicate_rows_pass_for_clean_trials(roundtrip):
    nwbfile = _new_nwbfile()
    for i in range(20):
        nwbfile.add_trial(start_time=float(i), stop_time=i + 0.5)
    assert check_duplicate_rows(roundtrip(nwbfile).trials) is None


def test_duplicate_rows_array_column_but_not_axis_column(roundtrip):
    rng = np.random.default_rng(2)
    nwbfile = _new_nwbfile()
    module = nwbfile.create_processing_module(name="ophys", description="ophys")
    curve = rng.normal(size=36)
    table = DynamicTable(
        name="tuning_curves",
        description="tuning curves",
        columns=[
            VectorData(name="curve", description="curve", data=np.tile(curve, (10, 1))),
            VectorData(name="bin", description="bin centers", data=np.tile(np.arange(36.0), (10, 1))),
        ],
    )
    module.add(table)
    messages = _messages(check_duplicate_rows(roundtrip(nwbfile).processing["ophys"]["tuning_curves"]))
    assert len(messages) == 1
    assert "Column 'curve'" in messages[0].message
