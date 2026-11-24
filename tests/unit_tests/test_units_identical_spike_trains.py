"""Tests for check_units_identical_spike_trains. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from pynwb import NWBHDF5IO, NWBFile

from nwbinspector import Importance
from nwbinspector.checks import check_units_identical_spike_trains


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


def test_units_identical_spike_trains(roundtrip):
    rng = np.random.default_rng(0)
    nwbfile = _new_nwbfile()
    trains = [np.sort(rng.uniform(0, 100, 50)) for _ in range(4)]
    for unit_id, train in enumerate(trains):
        nwbfile.add_unit(id=unit_id, spike_times=train)
    nwbfile.add_unit(id=2, spike_times=trains[2])  # the same unit stored twice under one id
    nwbfile.add_unit(id=7, spike_times=trains[3])  # the same train under a new id
    nwbfile.add_unit(id=8, spike_times=np.sort(rng.uniform(0, 100, 50)))  # same count, different train
    units = roundtrip(nwbfile).units

    messages = _messages(check_units_identical_spike_trains(units))
    assert len(messages) == 2
    assert all(m.importance == Importance.CRITICAL for m in messages)
    assert "id 2 (rows 2, 4)" in messages[0].message
    assert "ids 3, 7" in messages[1].message


def test_units_identical_spike_trains_pass_for_empty_and_distinct(roundtrip):
    nwbfile = _new_nwbfile()
    for unit_id in range(5):
        nwbfile.add_unit(id=unit_id, spike_times=[])
    for unit_id in range(5, 10):
        nwbfile.add_unit(id=unit_id, spike_times=[float(unit_id)])
    assert check_units_identical_spike_trains(roundtrip(nwbfile).units) is None
