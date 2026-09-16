"""Test the user experience when ``hdmf-zarr`` is not installed.

This file serves two roles:

1. **As a script** (``python tests/test_missing_hdmf_zarr.py``): generates the
   Zarr-backed NWB fixture used by the test. Requires ``hdmf-zarr`` and
   ``pynwb`` to be installed.
2. **As a pytest test**: reads the pre-generated fixture from disk and verifies
   that ``inspect_all`` raises ``ModuleNotFoundError`` with the install hint
   pointing at the offending path. Skips when ``hdmf-zarr`` is installed.

CI runs both roles in sequence: install with ``[zarr]`` -> run as script ->
uninstall ``hdmf-zarr`` -> run pytest.
"""

import importlib.util
import shutil
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import pytest

from nwbinspector import inspect_all

HDMF_ZARR_PRESENT = importlib.util.find_spec("hdmf_zarr") is not None

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "missing_hdmf_zarr"
ZARR_FIXTURE_PATH = FIXTURE_DIR / "session.nwb.zarr"

pytestmark = pytest.mark.skipif(
    HDMF_ZARR_PRESENT,
    reason="This test only runs when hdmf-zarr is NOT installed",
)


def _generate_zarr_fixture() -> int:
    """Generate the Zarr-backed NWB fixture. Requires ``hdmf-zarr`` to be installed."""
    try:
        from hdmf_zarr import NWBZarrIO
        from pynwb import NWBFile
    except ModuleNotFoundError as exc:
        print(
            f"Cannot generate fixture: {exc}. Install hdmf-zarr and pynwb first: " "`pip install hdmf-zarr pynwb`.",
            file=sys.stderr,
        )
        return 1

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    if ZARR_FIXTURE_PATH.exists():
        shutil.rmtree(ZARR_FIXTURE_PATH)

    nwbfile = NWBFile(
        session_description="",
        identifier=str(uuid4()),
        session_start_time=datetime(2025, 1, 1).astimezone(),
    )
    with NWBZarrIO(path=str(ZARR_FIXTURE_PATH), mode="w") as io:
        io.write(nwbfile)

    print(f"Wrote {ZARR_FIXTURE_PATH}")
    return 0


def test_inspect_all_on_zarr_path_raises_module_not_found_error():
    """Inspecting a folder containing a real Zarr-backed NWB file raises
    ``ModuleNotFoundError`` directly with an install-hint message that names
    the offending path, rather than silently returning zero files or burying
    the failure in an ``Importance.ERROR`` inspector message.

    Exercises the full pipeline: ``get_nwbfiles_from_path`` -> per-file
    ``read_nwbfile_and_io`` -> ``ModuleNotFoundError`` propagating up through
    ``inspect_nwbfiles`` and ``inspect_nwbfile``.
    """
    if not ZARR_FIXTURE_PATH.exists():
        pytest.skip(
            f"Zarr fixture not found at {ZARR_FIXTURE_PATH}. "
            f"Generate it with `python tests/test_missing_hdmf_zarr.py` "
            f"(requires hdmf-zarr to be installed)."
        )

    expected_error_message = (
        f"Reading the Zarr-backed NWB file at '{ZARR_FIXTURE_PATH}' requires the 'hdmf-zarr' package.\n"
        "Install it with `pip install nwbinspector[zarr]` or `pip install hdmf-zarr`."
    )

    with pytest.raises(ModuleNotFoundError) as excinfo:
        list(inspect_all(path=str(FIXTURE_DIR), skip_validate=True))

    assert str(excinfo.value) == expected_error_message


if __name__ == "__main__":
    raise SystemExit(_generate_zarr_fixture())
