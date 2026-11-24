"""Chunked scans for checking that one-dimensional arrays are in ascending order."""

from dataclasses import dataclass, field
from typing import Optional

import h5py
import numpy as np
from numpy.typing import ArrayLike

# An array whose bytes exceed this budget is scanned by sampling instead of in full.
# Local reads of a 1-D float64 array run at several hundred MB/s, so a full scan of the
# local budget costs on the order of a second. Streamed reads from DANDI run at a few
# tens of MB/s, so the remote budget is smaller.
DEFAULT_MAX_BYTES_LOCAL = 1_000_000_000
DEFAULT_MAX_BYTES_REMOTE = 200_000_000

# When an array is over budget, roughly this fraction of the budget is spent on sampled windows.
SAMPLE_FRACTION = 0.25

# Elements read per window. Rounded up to a multiple of the HDF5 chunk length when there is one.
DEFAULT_WINDOW_LENGTH = 1_048_576


@dataclass
class OrderScanResult:
    """Outcome of an ordering scan over a one-dimensional array."""

    n_total: int
    n_checked: int = 0
    sampled: bool = False
    # Positions ``i`` such that ``data[i] < data[i - 1]`` (the element that steps backwards).
    descending_positions: list = field(default_factory=list)
    n_descending: int = 0
    # Positions ``i`` such that ``data[i] == data[i - 1]``.
    first_equal_position: Optional[int] = None
    n_equal: int = 0

    @property
    def first_descending_position(self) -> Optional[int]:
        return self.descending_positions[0] if self.descending_positions else None


def is_remote_dataset(data: ArrayLike) -> bool:
    """Best guess at whether reads from this dataset go over the network."""
    # LINDI datasets subclass h5py.Dataset but have no HDF5 driver. LINDI is used to stream DANDI
    # assets through a precomputed JSON index, so treat it as remote.
    if type(data).__module__.split(".")[0] == "lindi":
        return True
    if isinstance(data, h5py.Dataset):
        try:
            return data.file.driver in ("fileobj", "ros3")
        except Exception:  # pragma: no cover - closed or unusual files
            return False
    store = getattr(data, "store", None)
    if store is not None:
        return "fsspec" in type(store).__name__.lower() or "remote" in type(store).__name__.lower()
    return False


def default_max_bytes(data: ArrayLike) -> int:
    return DEFAULT_MAX_BYTES_REMOTE if is_remote_dataset(data) else DEFAULT_MAX_BYTES_LOCAL


def _length_and_itemsize(data: ArrayLike) -> tuple[int, int]:
    if isinstance(data, (list, tuple)):
        data = np.asarray(data)
    length = len(data)
    dtype = getattr(data, "dtype", None)
    itemsize = np.dtype(dtype).itemsize if dtype is not None else 8
    return length, itemsize


def plan_windows(
    data: ArrayLike,
    max_bytes: Optional[int] = None,
    window_length: Optional[int] = None,
    seed: int = 0,
) -> tuple[list[tuple[int, int]], bool]:
    """
    Split ``range(len(data))`` into windows to read.

    Returns the windows and whether they are a sample. When the array fits the byte budget the windows
    cover the whole array. Otherwise they are the first window, the last window, and a reproducible
    random selection of windows in between that together use about ``SAMPLE_FRACTION`` of the budget.
    """
    n, itemsize = _length_and_itemsize(data)
    if n == 0:
        return [], False
    if max_bytes is None:
        max_bytes = default_max_bytes(data)

    if window_length is None:
        window_length = DEFAULT_WINDOW_LENGTH
        chunks = getattr(data, "chunks", None)
        if chunks:
            chunk_length = int(chunks[0])
            window_length = max(chunk_length, (window_length // chunk_length) * chunk_length)

    if n * itemsize <= max_bytes:
        return [(start, min(start + window_length, n)) for start in range(0, n, window_length)], False

    n_windows_total = int(np.ceil(n / window_length))
    n_sampled = max(2, int(SAMPLE_FRACTION * max_bytes // (window_length * itemsize)))
    middle = np.arange(1, n_windows_total - 1)
    rng = np.random.default_rng(seed)
    chosen = rng.choice(middle, size=min(len(middle), n_sampled - 2), replace=False) if len(middle) else []
    window_indices = sorted({0, n_windows_total - 1, *map(int, chosen)})
    return [(i * window_length, min((i + 1) * window_length, n)) for i in window_indices], True


def scan_ascending(
    data: ArrayLike,
    *,
    ignore_nan: bool = True,
    segment_starts: Optional[np.ndarray] = None,
    max_bytes: Optional[int] = None,
    window_length: Optional[int] = None,
    max_positions: int = 10_000,
) -> OrderScanResult:
    """
    Scan a one-dimensional array for steps where the value goes down or stays the same.

    The array is read window by window so memory use is bounded. Contiguous windows overlap by one
    element, so a step that crosses a window boundary is still seen.

    Parameters
    ----------
    data : array-like
        A one-dimensional h5py.Dataset, zarr array, numpy array or list.
    ignore_nan : bool
        Drop NaN values before comparing neighbors, so ``[1, nan, 0]`` counts as a descent from 1 to 0.
        When False, a comparison involving NaN is never counted as either a descent or an equality.
    segment_starts : array of int, optional
        Positions at which a new, independent segment begins (for example, the first spike of each unit
        in a ragged array). The step into a segment start is not counted.
    max_bytes : int, optional
        Byte budget for reading the whole array. Larger arrays are sampled; see ``plan_windows``.
        Defaults to ``DEFAULT_MAX_BYTES_LOCAL`` or ``DEFAULT_MAX_BYTES_REMOTE``.
    window_length : int, optional
        Number of elements per read.
    max_positions : int
        Keep at most this many descending positions (the count is always exact over what was read).
    """
    if isinstance(data, (list, tuple)):
        data = np.asarray(data)
    n = len(data)
    result = OrderScanResult(n_total=n)
    windows, sampled = plan_windows(data=data, max_bytes=max_bytes, window_length=window_length)
    result.sampled = sampled

    if segment_starts is not None:
        segment_starts = np.unique(np.asarray(segment_starts, dtype=np.int64))

    previous_window_stop = None
    carried_value = None  # last valid value read so far, used when windows are contiguous
    carried_position = None
    for start, stop in windows:
        contiguous = previous_window_stop == start
        values = np.asarray(data[start:stop])
        if values.ndim != 1:
            values = values.reshape(len(values), -1)[:, 0]
        if values.dtype.kind == "u":  # differences of unsigned integers would wrap around instead of going negative
            values = values.astype(np.int64)
        # Positions are implicit (base, base + 1, ...) unless NaNs are dropped, which is the rare case.
        base = start
        positions = None

        if contiguous and carried_value is not None:
            values = np.concatenate([np.asarray([carried_value], dtype=values.dtype), values])
            if carried_position == start - 1:
                base = start - 1
            else:
                positions = np.concatenate([[carried_position], np.arange(start, stop, dtype=np.int64)])
        elif not contiguous and start > 0:
            # A sampled window: also read the element just before it so the first step is checked.
            previous = np.asarray(data[start - 1 : start]).ravel()[:1]
            values = np.concatenate([previous.astype(values.dtype), values])
            base = start - 1

        if ignore_nan and np.issubdtype(values.dtype, np.floating):
            is_valid = ~np.isnan(values)
            if not is_valid.all():
                if positions is None:
                    positions = np.arange(base, base + len(values), dtype=np.int64)
                values = values[is_valid]
                positions = positions[is_valid]

        result.n_checked += stop - start
        previous_window_stop = stop
        if len(values) >= 1:
            carried_value = values[-1]
            carried_position = int(positions[-1]) if positions is not None else base + len(values) - 1
        if len(values) < 2:
            continue

        with np.errstate(invalid="ignore"):
            steps = np.diff(values)
        descending = steps < 0
        equal = steps == 0

        # Step k arrives at position base + k + 1 (or positions[k + 1] when NaNs were dropped).
        if positions is None:
            first_position, last_position = base, base + len(values) - 1
        else:
            first_position, last_position = int(positions[0]), int(positions[-1])
        if segment_starts is not None and len(segment_starts):
            lo, hi = np.searchsorted(segment_starts, [first_position + 1, last_position + 1])
            starts_here = segment_starts[lo:hi]
            if len(starts_here):
                if positions is None:
                    step_indices = starts_here - base - 1
                else:
                    step_indices = np.flatnonzero(np.isin(positions[1:], starts_here))
                descending[step_indices] = False
                equal[step_indices] = False

        n_descending = int(np.count_nonzero(descending))
        if n_descending:
            result.n_descending += n_descending
            room = max_positions - len(result.descending_positions)
            if room > 0:
                step_indices = np.flatnonzero(descending)[:room]
                found = step_indices + base + 1 if positions is None else positions[1:][step_indices]
                result.descending_positions.extend(found.tolist())
        n_equal = int(np.count_nonzero(equal))
        if n_equal:
            result.n_equal += n_equal
            if result.first_equal_position is None:
                first = int(np.flatnonzero(equal)[0])
                result.first_equal_position = first + base + 1 if positions is None else int(positions[first + 1])

    return result
