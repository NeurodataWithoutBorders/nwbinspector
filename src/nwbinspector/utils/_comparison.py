"""
Helpers for checks that compare data within one file (rows, columns, series and times), for example to find data
that were stored twice.

The duplicated-data checks each carry an identical copy of this module, so that they can be reviewed and merged
one at a time.
"""

import hashlib
from typing import Any, Iterable, Optional

import h5py
import numpy as np
from hdmf.common import DynamicTable, VectorIndex

# Datasets at or below this size are read and compared whole; larger ones are sampled.
FULL_READ_BYTES = 32 * 1024**2
# Size of each sampled block along the first axis, in bytes.
BLOCK_BYTES = 1024**2
# Number of sampled blocks for a dataset too large to read whole.
N_BLOCKS = 5
# Largest table (rows) that a row or column comparison reads.
MAX_TABLE_ROWS = 2_000_000
# Columns need at least this many distinct values to be compared with each other.
MIN_DISTINCT_FOR_COLUMNS = 3
# Repeated times are reported when they are at least this fraction of the values.
MIN_REPEAT_FRACTION = 0.01
# How many examples to list in a message.
N_EXAMPLES = 5

# Data that the checks read: a numpy array, an h5py.Dataset, a zarr array or a list.
DataLike = Any


def h5_dataset(obj: Any) -> Optional[h5py.Dataset]:
    """Return obj if it is an h5py.Dataset, otherwise None."""
    return obj if isinstance(obj, h5py.Dataset) else None


def data_shape(data: Any) -> tuple:
    """Shape of a dataset or array-like without reading it."""
    return tuple(data.shape) if hasattr(data, "shape") else np.asarray(data).shape


def data_dtype(data: Any) -> np.dtype:
    """Data type of a dataset or array-like without reading it."""
    dt = getattr(data, "dtype", None)
    if dt is None:
        return np.asarray(data).dtype
    try:
        return np.dtype(dt)
    except TypeError:
        return np.dtype(object)  # hdmf string wrappers report dtype as a str


def is_reference_dtype(dtype: Any) -> bool:
    """True for HDF5 object reference data types."""
    try:
        return h5py.check_dtype(ref=dtype) is not None
    except Exception:
        return False


def as_bytes(arr: Any) -> bytes:
    """Bytes of an array, for hashing. Object arrays (strings) are hashed through their repr."""
    arr = np.asarray(arr)
    if arr.dtype.kind == "O":
        return repr(arr.tolist()).encode()
    return np.ascontiguousarray(arr).tobytes()


def digest(arr: Any) -> str:
    """Short hash of an array's values."""
    return hashlib.blake2b(as_bytes(arr), digest_size=16).hexdigest()


def is_constant(arr: Any) -> bool:
    """True when every element of an array has the same value (all NaN counts as constant)."""
    arr = np.asarray(arr)
    if arr.size <= 1:
        return True
    if arr.dtype.kind == "f":
        nan = np.isnan(arr)
        if nan.all():
            return True
        if nan.any():
            return False
    try:
        flat = arr.reshape(-1)
        return bool((flat == flat[0]).all())
    except Exception:
        return len(set(map(repr, arr.reshape(-1).tolist()))) <= 1


def sample_blocks(data: Any, block_bytes: int = BLOCK_BYTES, n_blocks: int = N_BLOCKS) -> list[tuple]:
    """
    Index tuples that sample a large dataset at n_blocks evenly spaced places along axis 0, each holding at most
    about block_bytes (trailing axes are cut down for very wide rows, such as imaging frames).
    """
    shape = data_shape(data)
    itemsize = data_dtype(data).itemsize
    dims = list(shape)
    row_bytes = int(np.prod(dims[1:], dtype=np.int64)) * itemsize
    k = max(1, min(shape[0], block_bytes // max(1, row_bytes)))
    dims[0] = k
    while int(np.prod(dims, dtype=np.int64)) * itemsize > block_bytes and max(dims[1:], default=1) > 1:
        j = 1 + int(np.argmax(dims[1:]))
        dims[j] = max(1, dims[j] // 2)
    starts = sorted(set(int(s) for s in np.linspace(0, max(0, shape[0] - k), n_blocks)))
    tail = tuple(slice(0, d) for d in dims[1:])
    return [(slice(s, s + k),) + tail for s in starts]


def format_examples(items: Iterable, n: int = N_EXAMPLES) -> str:
    """Comma-separated list of the first n items, saying how many more there are."""
    items = list(items)
    text = ", ".join(str(i) for i in items[:n])
    return text + (f", and {len(items) - n} more" if len(items) > n else "")


def plain_columns(table: DynamicTable) -> list:
    """Non-ragged columns of a table (index columns and the columns they index are left out)."""
    indexed = {id(col.target) for col in table.columns if isinstance(col, VectorIndex)}
    return [col for col in table.columns if not isinstance(col, VectorIndex) and id(col) not in indexed]


def is_coarse_resolution(values: Any, step: float = 1e-3) -> bool:
    """True when every time is a multiple of step (1 ms) or coarser, so two events can share a value."""
    v = np.asarray(values, dtype=float).reshape(-1)
    v = v[np.isfinite(v)][:100_000]
    if v.size == 0:
        return False
    return bool(np.allclose(v / step, np.round(v / step), rtol=0, atol=1e-3))


def count_repeats(values: Any) -> int:
    """Number of values that equal another value in the same array (NaN is ignored)."""
    v = np.asarray(values).reshape(-1)
    if v.dtype.kind == "f":
        v = v[~np.isnan(v)]
    if v.size < 2:
        return 0
    v = np.sort(v, kind="stable")
    return int(np.count_nonzero(v[1:] == v[:-1]))
