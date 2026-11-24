"""Tests for the check that finds the same primary data in more than one file of a folder."""

from datetime import datetime
from pathlib import Path
from uuid import uuid4

import numpy as np
import pytest
from pynwb import NWBHDF5IO, NWBFile, TimeSeries
from pynwb.file import Subject

from nwbinspector import Importance, inspect_all
from nwbinspector._duplicate_data import (
    CHECK_DUPLICATE_DATA_ACROSS_FILES,
    _fingerprint_array,
    check_duplicate_data_across_files,
)


def _make_nwbfile(subject_id: str) -> NWBFile:
    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime(2020, 1, 1).astimezone(),
        subject=Subject(subject_id=subject_id, species="Mus musculus", sex="U", age="P90D"),
    )
    return nwbfile


def _write(nwbfile: NWBFile, path: Path) -> None:
    with NWBHDF5IO(path=str(path), mode="w") as io:
        io.write(nwbfile)


def _add_series(nwbfile: NWBFile, name: str, data: np.ndarray, stimulus: bool = False) -> None:
    series = TimeSeries(name=name, data=data, unit="volts", rate=1000.0)
    if stimulus:
        nwbfile.add_stimulus(series)
    else:
        nwbfile.add_acquisition(series)


def _messages(folder: Path, **kwargs) -> list:
    return [
        message
        for message in inspect_all(path=folder, progress_bar=False, skip_validate=True, **kwargs)
        if message.check_function_name == CHECK_DUPLICATE_DATA_ACROSS_FILES
    ]


def test_same_recording_with_different_units_is_a_partial_match(tmp_path):
    rng = np.random.default_rng(seed=0)
    recording = rng.normal(size=(5000, 4))
    for subject_id in ("rat1", "rat2"):
        nwbfile = _make_nwbfile(subject_id=subject_id)
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=recording)
        nwbfile.add_unit(spike_times=np.sort(rng.uniform(0, 5, size=200)))
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-{subject_id}.nwb")

    # The spike times differ between the two files, so only the recording matches
    messages = _messages(folder=tmp_path)
    assert len(messages) == 1
    assert messages[0].importance == Importance.BEST_PRACTICE_SUGGESTION


def test_whole_file_copy_is_critical(tmp_path):
    rng = np.random.default_rng(seed=0)
    recording = rng.normal(size=(5000, 4))
    spike_times = [np.sort(rng.uniform(0, 5, size=200)) for _ in range(3)]
    for subject_id in ("rat1", "rat2"):
        nwbfile = _make_nwbfile(subject_id=subject_id)
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=recording)
        for unit_spike_times in spike_times:
            nwbfile.add_unit(spike_times=unit_spike_times)
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-{subject_id}.nwb")

    messages = _messages(folder=tmp_path)
    assert len(messages) == 1
    assert messages[0].importance == Importance.CRITICAL
    assert "sub-rat1.nwb" in messages[0].message and "sub-rat2.nwb" in messages[0].message
    assert "/acquisition/ElectricalSeries/data" in messages[0].message
    assert "/units/spike_times" in messages[0].message


def test_partial_match_names_the_shared_array(tmp_path):
    rng = np.random.default_rng(seed=0)
    position = rng.normal(size=(3000, 2))
    for probe in ("probe0", "probe1"):
        nwbfile = _make_nwbfile(subject_id="mouse1")
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=rng.normal(size=(5000, 4)))
        _add_series(nwbfile=nwbfile, name="Position", data=position)
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-mouse1_{probe}.nwb")

    messages = _messages(folder=tmp_path)
    assert len(messages) == 1
    assert messages[0].importance == Importance.BEST_PRACTICE_SUGGESTION
    assert "/acquisition/Position/data" in messages[0].message

    # Raising the threshold to CRITICAL hides the partial match
    assert _messages(folder=tmp_path, importance_threshold=Importance.CRITICAL) == []


def test_shared_stimulus_is_not_reported(tmp_path):
    rng = np.random.default_rng(seed=0)
    stimulus = rng.normal(size=(5000,))
    for subject_id in ("mouse1", "mouse2"):
        nwbfile = _make_nwbfile(subject_id=subject_id)
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=rng.normal(size=(5000, 4)))
        _add_series(nwbfile=nwbfile, name="Stimulus", data=stimulus, stimulus=True)
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-{subject_id}.nwb")

    assert _messages(folder=tmp_path) == []


def test_constant_and_small_arrays_are_not_reported(tmp_path):
    rng = np.random.default_rng(seed=0)
    for subject_id in ("mouse1", "mouse2"):
        nwbfile = _make_nwbfile(subject_id=subject_id)
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=rng.normal(size=(5000, 4)))
        _add_series(nwbfile=nwbfile, name="Flat", data=np.zeros(5000))
        _add_series(nwbfile=nwbfile, name="Short", data=np.arange(10, dtype=float))
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-{subject_id}.nwb")

    assert _messages(folder=tmp_path) == []


def test_arrays_sharing_only_a_leading_segment_do_not_match():
    rng = np.random.default_rng(seed=0)
    first = np.concatenate([np.zeros(10_000), rng.normal(size=90_000)])
    second = np.concatenate([np.zeros(10_000), rng.normal(size=90_000)])
    assert _fingerprint_array(first) != _fingerprint_array(second)
    assert _fingerprint_array(first) == _fingerprint_array(first.copy())


def test_check_can_be_ignored_or_left_unselected(tmp_path):
    rng = np.random.default_rng(seed=0)
    recording = rng.normal(size=(5000, 4))
    for subject_id in ("rat1", "rat2"):
        nwbfile = _make_nwbfile(subject_id=subject_id)
        _add_series(nwbfile=nwbfile, name="ElectricalSeries", data=recording)
        _write(nwbfile=nwbfile, path=tmp_path / f"sub-{subject_id}.nwb")

    assert len(_messages(folder=tmp_path)) == 1
    assert _messages(folder=tmp_path, ignore=[CHECK_DUPLICATE_DATA_ACROSS_FILES]) == []
    assert _messages(folder=tmp_path, select=["check_data_orientation"]) == []
    assert len(_messages(folder=tmp_path, select=[CHECK_DUPLICATE_DATA_ACROSS_FILES])) == 1


def test_grouping_reports_each_set_of_files_once():
    fingerprints_by_file = {
        "a.nwb": {"x": ["/acquisition/A/data"], "y": ["/acquisition/B/data"]},
        "b.nwb": {"x": ["/acquisition/A/data"], "y": ["/acquisition/B/data"]},
        "c.nwb": {"x": ["/acquisition/A/data"], "z": ["/acquisition/C/data"]},
        "d.nwb": {"w": ["/acquisition/D/data"]},
    }
    messages = list(check_duplicate_data_across_files(fingerprints_by_file=fingerprints_by_file))
    importances = sorted(message.importance.name for message in messages)
    # a and b match completely; a, b and c share one array
    assert importances == ["BEST_PRACTICE_SUGGESTION", "CRITICAL"]
    critical = next(message for message in messages if message.importance == Importance.CRITICAL)
    assert "['a.nwb', 'b.nwb']" in critical.message
    suggestion = next(message for message in messages if message.importance != Importance.CRITICAL)
    assert "['a.nwb', 'b.nwb', 'c.nwb']" in suggestion.message
