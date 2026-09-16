Data Storage
============

The advice on this page applies to any dataset in the file, whatever container holds it. The layout chosen when a
dataset is written, whether it is contiguous or chunked, how it is chunked, and whether it is compressed, decides how
much space the file takes and how quickly a reader can get at a slice of it. This matters most for files that are
intended to be uploaded to the :dandi-archive:`DANDI Archive <>` for storage, sharing, and publication, where readers
often stream a small part of a large file over the network.


.. _best_practice_chunk_data:

Chunk Data
----------

Use chunking to optimize reading of large data for your use case.

By default, when using the HDF5 backend, datasets are stored on disk contiguously in row-major order. For the ``data``
of a :ref:`nwb-schema:sec-TimeSeries` with multiple dimensions, this means all data from a single timestamp are stored
together on disk, followed by the next timestamp, and so on.

This storage scheme may be optimal for certain uses, such as slicing a :ref:`nwb-schema:sec-TimeSeries` by time;
however, it may be sub-optimal for other uses, such as reading data from all timestamps for a particular value in the
second or third dimension. Chunking lets the writer pick a layout that suits how the data will be read, and it is a
prerequisite for compression.

For more information about how to enable chunking and compression on your data, consult the
:pynwb-docs:`PyNWB tutorial <tutorials/advanced_io/h5dataio.html#chunking>` or the
`MatNWB instructions <https://matnwb.readthedocs.io/en/latest/pages/tutorials/dataPipe.html>`_.

A dataset written as one chunk that covers the whole array has the overhead of chunked storage without its benefits.
Small datasets of that kind are better stored contiguously, and large ones should be split into several chunks and
compressed.

Check function: :py:meth:`~nwbinspector.checks._nwb_containers.check_single_chunk_dataset`



.. _best_practice_compression:

Compress Data
-------------

Data writers can optimize the storage of large data arrays for particular uses by using compression applied to each
chunk individually. This is especially important when writing NWBFiles that are intended to be uploaded to the
:dandi-archive:`DANDI Archive <>` for storage, sharing, and publication. For more information about how to enable
compression on your data, consult the
:pynwb-docs:`PyNWB tutorial <tutorials/advanced_io/h5dataio.html#compression-and-other-i-o-filters>` or the
`MatNWB instructions <https://matnwb.readthedocs.io/en/latest/pages/tutorials/dataPipe.html>`_.

Check functions: :py:meth:`~nwbinspector.checks._nwb_containers.check_large_dataset_compression`,
:py:meth:`~nwbinspector.checks._nwb_containers.check_small_dataset_compression`
