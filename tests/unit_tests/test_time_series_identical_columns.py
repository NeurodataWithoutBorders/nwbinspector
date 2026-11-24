"""Tests for check_time_series_identical_columns. Each case is written to an HDF5 file and read back, since the check
looks at the data as stored on disk."""

from datetime import datetime, timezone

import numpy as np
import pytest
from hdmf.backends.hdf5 import H5DataIO
from pynwb import NWBHDF5IO, NWBFile, TimeSeries
from pynwb.behavior import Position, SpatialSeries

from nwbinspector import Importance
from nwbinspector.checks import check_time_series_identical_columns
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


def test_time_series_identical_columns(roundtrip):
    rng = np.random.default_rng(7)
    nwbfile = _new_nwbfile()
    xy = rng.normal(size=(1000, 2))
    position = Position(
        spatial_series=SpatialSeries(name="position", data=np.c_[xy, xy[:, 1]], reference_frame="origin", rate=30.0)
    )
    nwbfile.create_processing_module(name="behavior", description="behavior").add(position)
    series = roundtrip(nwbfile).processing["behavior"]["Position"]["position"]
    message = check_time_series_identical_columns(series)
    assert message is not None
    assert message.importance == Importance.BEST_PRACTICE_VIOLATION
    assert "columns 1 = 2" in message.message


def test_time_series_identical_columns_pass_for_distinct_columns(roundtrip):
    rng = np.random.default_rng(14)
    nwbfile = _new_nwbfile()
    nwbfile.add_acquisition(TimeSeries(name="raw", data=rng.normal(size=(1000, 8)), unit="V", rate=1000.0))
    assert check_time_series_identical_columns(roundtrip(nwbfile).acquisition["raw"]) is None


def test_time_series_identical_columns_sampled_and_chunked(roundtrip, monkeypatch):
    monkeypatch.setattr(_comparison, "FULL_READ_BYTES", 64 * 1024)
    rng = np.random.default_rng(8)
    nwbfile = _new_nwbfile()
    data = rng.normal(size=(100_000, 6)).astype("float32")
    data[:, 4] = data[:, 2]
    data[90_000:, 5] = data[90_000:, 1]  # matches column 1 only at the end, so the first block rules it out
    nwbfile.add_acquisition(TimeSeries(name="big", data=H5DataIO(data, chunks=(16384, 2)), unit="V", rate=1000.0))
    series = roundtrip(nwbfile).acquisition["big"]

    message = check_time_series_identical_columns(series)
    assert message is not None
    assert "columns 2 = 4" in message.message and "sampled" in message.message
    # A budget smaller than one block of chunks skips the series.
    assert check_time_series_identical_columns(series, max_fetch_bytes=1024) is None
