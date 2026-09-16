import time
from datetime import datetime
from uuid import uuid4

import numpy as np
import pynwb
from hdmf.testing import TestCase

from nwbinspector import Importance, InspectorMessage, Severity, organize_messages
from nwbinspector.tools import all_of_type, get_s3_urls_and_dandi_paths


def test_all_of_type():
    nwbfile = pynwb.NWBFile(
        session_description="Testing inspector.",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    true_time_series = [
        pynwb.TimeSeries(name=f"time_series_{x}", data=np.zeros(shape=(100, 10)), rate=1.0, unit="") for x in range(4)
    ]
    for x in range(2):
        nwbfile.add_acquisition(true_time_series[x])
    ecephys_module = nwbfile.create_processing_module(name="ecephys", description="")
    ecephys_module.add(true_time_series[2])
    ophys_module = nwbfile.create_processing_module(name="ophys", description="")
    ophys_module.add(true_time_series[3])

    nwbfile_time_series = [obj for obj in all_of_type(nwbfile=nwbfile, neurodata_type=pynwb.TimeSeries)]
    for time_series in true_time_series:
        assert time_series in nwbfile_time_series


class TestOrganization(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.messages = [
            InspectorMessage(
                message="test1",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                check_function_name="fun1",
                object_type="ElectricalSeries",
                object_name="ts1",
                location="/acquisition/",
                file_path="path1/file1.nwb",
            ),
            InspectorMessage(
                message="test2",
                importance=Importance.CRITICAL,
                check_function_name="fun2",
                object_type="DynamicTable",
                object_name="tab",
                location="/acquisition/",
                file_path="path1/file1.nwb",
            ),
            InspectorMessage(
                message="test3",
                importance=Importance.BEST_PRACTICE_SUGGESTION,
                severity=Severity.HIGH,
                check_function_name="fun3",
                object_type="NWBFile",
                object_name="root",
                location="/",
                file_path="path2/file2.nwb",
            ),
            InspectorMessage(
                message="test4",
                importance=Importance.CRITICAL,
                check_function_name="fun2",
                object_type="ElectricalSeries",
                object_name="ts1",
                location="/processing/ecephys/LFP/",
                file_path="path2/path3/file3.nwb",
            ),
        ]

    def test_message_level_assertion(self):
        for level in ["message", "object_name", "severity"]:
            with self.assertRaisesWith(
                exc_type=AssertionError,
                exc_msg=(
                    "You must specify levels to organize by that correspond to attributes of the InspectorMessage "
                    "class, excluding the text message, object_name, and severity."
                ),
            ):
                organize_messages(messages=self.messages, levels=[level])

    def test_file_by_importance(self):
        test_result = organize_messages(messages=self.messages, levels=["file_path", "importance"])
        true_result = {
            "path1/file1.nwb": {
                Importance.CRITICAL: [
                    InspectorMessage(
                        message="test2",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="DynamicTable",
                        object_name="tab",
                        location="/acquisition/",
                        file_path="path1/file1.nwb",
                    )
                ],
                Importance.BEST_PRACTICE_SUGGESTION: [
                    InspectorMessage(
                        message="test1",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.LOW,
                        check_function_name="fun1",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/acquisition/",
                        file_path="path1/file1.nwb",
                    )
                ],
            },
            "path2/file2.nwb": {
                Importance.BEST_PRACTICE_SUGGESTION: [
                    InspectorMessage(
                        message="test3",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.HIGH,
                        check_function_name="fun3",
                        object_type="NWBFile",
                        object_name="root",
                        location="/",
                        file_path="path2/file2.nwb",
                    )
                ]
            },
            "path2/path3/file3.nwb": {
                Importance.CRITICAL: [
                    InspectorMessage(
                        message="test4",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/processing/ecephys/LFP/",
                        file_path="path2/path3/file3.nwb",
                    )
                ]
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)

    def test_reverse(self):
        test_result = organize_messages(
            messages=self.messages, levels=["importance", "file_path"], reverse=[False, True]
        )
        true_result = {
            Importance.CRITICAL: {
                "path2/path3/file3.nwb": [
                    InspectorMessage(
                        message="test4",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/processing/ecephys/LFP/",
                        file_path="path2/path3/file3.nwb",
                    )
                ],
                "path1/file1.nwb": [
                    InspectorMessage(
                        message="test2",
                        importance=Importance.CRITICAL,
                        severity=Severity.LOW,
                        check_function_name="fun2",
                        object_type="DynamicTable",
                        object_name="tab",
                        location="/acquisition/",
                        file_path="path1/file1.nwb",
                    )
                ],
            },
            Importance.BEST_PRACTICE_SUGGESTION: {
                "path2/file2.nwb": [
                    InspectorMessage(
                        message="test3",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.HIGH,
                        check_function_name="fun3",
                        object_type="NWBFile",
                        object_name="root",
                        location="/",
                        file_path="path2/file2.nwb",
                    )
                ],
                "path1/file1.nwb": [
                    InspectorMessage(
                        message="test1",
                        importance=Importance.BEST_PRACTICE_SUGGESTION,
                        severity=Severity.LOW,
                        check_function_name="fun1",
                        object_type="ElectricalSeries",
                        object_name="ts1",
                        location="/acquisition/",
                        file_path="path1/file1.nwb",
                    )
                ],
            },
        }
        self.assertDictEqual(d1=test_result, d2=true_result)


class _FakeRemoteAsset:
    """Stand-in for dandi.dandiapi.BaseRemoteAsset that records when its content URL was resolved."""

    def __init__(self, path: str, delay: float = 0.0):
        self.path = path
        self.delay = delay

    def get_content_url(self, follow_redirects: int = 1, strip_query: bool = True) -> str:
        start = time.time()
        time.sleep(self.delay)
        end = time.time()
        return (
            f"https://fake.s3/{self.path}#start={start}&end={end}"
            f"&follow_redirects={follow_redirects}&strip_query={strip_query}"
        )


class _FakeRemoteDandiset:
    def __init__(self, assets: list):
        self._assets = assets

    def get_assets(self):
        return iter(self._assets)


class _FakeDandiAPIClient:
    def __init__(self, assets: list):
        self._assets = assets

    def get_dandiset(self, dandiset_id: str, version_id=None):
        return _FakeRemoteDandiset(assets=self._assets)


def _parse_fake_url(url: str) -> dict:
    fragment = url.split("#", 1)[1]
    return dict(pair.split("=") for pair in fragment.split("&"))


def test_get_s3_urls_and_dandi_paths_serial():
    assets = [_FakeRemoteAsset(path=f"sub-{j}/sub-{j}.nwb") for j in range(3)]
    assets.append(_FakeRemoteAsset(path="dandiset.yaml"))
    client = _FakeDandiAPIClient(assets=assets)

    result = get_s3_urls_and_dandi_paths(dandiset_id="000000", n_jobs=1, client=client)

    assert sorted(result.values()) == [f"sub-{j}/sub-{j}.nwb" for j in range(3)]
    for url, path in result.items():
        assert url.startswith(f"https://fake.s3/{path}#")
        parsed = _parse_fake_url(url)
        assert parsed["follow_redirects"] == "1"
        assert parsed["strip_query"] == "True"


def test_get_s3_urls_and_dandi_paths_parallel():
    """Regression test: the parallel branch used to wait on every future after each submit, serializing the work."""
    delay = 0.5
    assets = [_FakeRemoteAsset(path=f"sub-{j}/sub-{j}.nwb", delay=delay) for j in range(4)]
    client = _FakeDandiAPIClient(assets=assets)

    result = get_s3_urls_and_dandi_paths(dandiset_id="000000", n_jobs=2, client=client)

    assert sorted(result.values()) == [f"sub-{j}/sub-{j}.nwb" for j in range(4)]

    intervals = [(float(p["start"]), float(p["end"])) for p in map(_parse_fake_url, result)]
    overlapping_pairs = [
        (a, b) for i, a in enumerate(intervals) for b in intervals[i + 1 :] if a[0] < b[1] and b[0] < a[1]
    ]
    assert overlapping_pairs, "No two content URL requests ran concurrently; the parallel branch is serialized."
