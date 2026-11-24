"""Tests for check_identical_columns. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from hdmf.common import DynamicTable, VectorData
from pynwb import NWBHDF5IO, NWBFile

from nwbinspector import Importance
from nwbinspector.checks import check_identical_columns


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


def test_identical_columns(roundtrip):
    rng = np.random.default_rng(6)
    nwbfile = _new_nwbfile()
    y = rng.normal(size=64)
    table = DynamicTable(
        name="coordinates",
        description="coordinates",
        columns=[
            VectorData(name="x", description="x", data=rng.normal(size=64)),
            VectorData(name="y", description="y", data=y),
            VectorData(name="z", description="z", data=y.copy()),
            VectorData(name="good", description="flag", data=np.ones(64, dtype=bool)),
            VectorData(name="good2", description="flag", data=np.ones(64, dtype=bool)),
            VectorData(name="stop_time", description="time", data=y + 10),
            VectorData(name="return_stop_time", description="time", data=y + 10),
        ],
    )
    nwbfile.add_acquisition(table)
    messages = _messages(check_identical_columns(roundtrip(nwbfile).acquisition["coordinates"]))
    assert len(messages) == 1
    assert messages[0].importance == Importance.CRITICAL
    assert "'y', 'z'" in messages[0].message


def test_identical_columns_pass_for_distinct_columns(roundtrip):
    rng = np.random.default_rng(13)
    nwbfile = _new_nwbfile()
    for i in range(10):
        nwbfile.add_trial(start_time=float(i), stop_time=i + rng.uniform(0.1, 0.9))
    assert check_identical_columns(roundtrip(nwbfile).trials) is None
