import math

import h5py
import subprocess

import numpy as np


def get_new_chunk_shape(dataset, target_size_mb=10.0, shape=(None, None, 32)):
    """Get a new chunk shape by attempting to scale up/down the current dataset chunks, bounded by the dataset size"""
    # Compute the current chunk size in MB
    current_chunk_size_mb = dataset.dtype.itemsize * np.prod(dataset.chunks) / 1024**2

    # Calculate the scaling factor to reach the target size
    scaling_factor = target_size_mb / current_chunk_size_mb

    # Compute the new chunk shape
    new_chunk_shape = []
    for i, (dim, dataset_shape_dim) in enumerate(zip(dataset.chunks, dataset.shape)):
        # take the nth root of the scaling factor where n is the number of dimensions left
        dimension_scaling_factor = math.pow(scaling_factor, 1 / (len(dataset.shape) - i))

        new_dim = min(int(dim * dimension_scaling_factor), dataset_shape_dim)

        new_chunk_shape.append(new_dim)

        # Calculate the scaling factor to reach the target size
        scaling_factor = scaling_factor / new_dim

    return new_chunk_shape


def get_chunk_size_mb(dataset):
    return np.prod(dataset.chunks) * dataset.dtype.itemsize / 1024**2


def repack_hdf5(
    input_file,
    output_file,
    target_chunk_size_mb=10,
    min_chunk_size_mb=5,
    max_chunk_size_mb=20,
    min_unchunked_dataset_size_gb=1,
    compression_str="GZIP=4",
    fs_page=True,
):
    # List to hold datasets that need to be repacked
    datasets_to_repack = []

    # Open the HDF5 file and check the chunks of each dataset
    with h5py.File(input_file, "r") as f:
        for name, dataset in f.items():
            if (
                not isinstance(dataset, h5py.Dataset)  # not a dataset
                or np.prod(dataset.shape) * dataset.dtype.itemsize / 1024**3 < min_unchunked_dataset_size_gb
                or dataset.chunks and (min_chunk_size_mb < get_chunk_size_mb(dataset) < max_chunk_size_mb)
            ):
                continue

            new_chunk_shape = get_new_chunk_shape(dataset, target_chunk_size_mb)
            datasets_to_repack.append((name, new_chunk_shape))

    # Build the command for h5repack
    cmd = ["h5repack"]
    if fs_page:
        # maybe add test here to see if paging is already enabled at a reasonable size
        cmd.extend(["-S", "PAGE", "-G", str(5*1024**2)])
    for name, new_chunk_shape in datasets_to_repack:
        cmd.extend(["-l", f"{name}:CHUNK={'x'.join(map(str, new_chunk_shape))};{compression_str}"])

    cmd.extend([input_file, output_file])

    # Run the command
    result = subprocess.run(cmd, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode != 0:
        print("Error executing command:", result.stderr)
    else:
        print("Command executed successfully")

