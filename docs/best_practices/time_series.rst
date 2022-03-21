Time Series
===========

When using ``TimeSeries`` or any of its descendants, please ensure the following practices are followed.

Note that these extend to any general subtype, such as ``ElectricalSeries``, ``SpatialSeries``, ``ImageSeries``, etc.



.. _best_practice_data_orientation:

Data Orientation
~~~~~~~~~~~~~~~~

The time dimension always goes first. In TimeSeries.data, the first dimension on the disk is always time.

Keep in mind that the dimensions are reversed in MatNWB, so in memory in MatNWB the time dimension must be last.

In PyNWB the order of the dimensions is the same in memory as on disk, so the time index should be first.

Check functions: :py:meth:`~nwbinspector.checks.time_series.check_data_orientation` and
:py:meth:`~nwbinspector.checks.time_series.check_timestamps_match_first_dimension`



.. _best_practice_unit_of_measurement

Units of Measurement
~~~~~~~~~~~~~~~~~~~~

Time-related values should always in seconds. This include ``rate`` (if applicable), which should should be in Hz.

Every TimeSeries instance has a ``unit`` as an attribute of the ``Dataset``, which is meant to indicate the unit of
measurement for that data, using the appropriate type from the 
`International System of Units (SI) <https://en.wikipedia.org/wiki/International_System_of_Units>`_



.. _best_practice_time_series_global_time_reference

Global Time Reference
~~~~~~~~~~~~~~~~~~~~~

``timestamps`` or ``starting_time`` should be in seconds with respect to the global ``timestamps_reference_time`` of the NWBFile.



.. _best_practice_time_series_subtypes

Subtypes
~~~~~~~~

ElectrialSeries are reserved for neural data. ElectrialSeries holds signal from electrodes positioned in or around the 
brain that are monitoring neural activity, and only those electrodes should be in the electrodes table.

For non-neural electrodes that still may store and report raw values in Volts, simply use a general ``TimeSeries`` 
object with ``unit`` set to ``Volts``.



.. _best_practice_timestamps_ascending

Breaks in Continuity
~~~~~~~~~~~~~~~~~~~~
TimeSeries data should generally be stored as one continuous stream as it was acquired, not by trial as is often 
reshaped for analysis.

Data can be trial-aligned on-the-fly using the ``trials`` table.

Storing measured data as a continuous stream ensures that other users have access to the inter-trial data, and that we 
can align the data within any specifiable window.

If you only have data spanning specific segments of time, then only include those timepoints in the data, see 
:ref:`best_practice_regular_timestamps` for more information.

A primary implication is that the values in ``timestamps``, as well as the corresponding ordering of their indices 
in the ``data`` array, should always be strictly increasing.

Check function: :py:meth:`~nwbinspector.checks.time_series.check_timestamps_ascending`



.. _best_practice_regular_timestamps:

Timestamps vs. Start & Rate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

``TimeSeries`` allows you to specify time using either ``timestamps`` or ``rate`` together with ``starting_time`` 
(which defaults to 0).

If the sampling rate is constant, then specify the ``rate`` and ``starting_time`` instead of writing the full ``timestamps`` vector.

For segmented data, refer to the section covering :ref:`best_practice_time_series_break_in_continuity`;

    1. If the sampling rate is constant within each segment, each segment can be written as a separate ``TimeSeries``
    with the ``starting_time`` incremented appropriately.
    2. Even if the sampling rate is constant within each segment, a single ``TimeSeries`` can be written using the 
    ``timestamps`` vector to appropriately indicate the gaps between segments.

Check function: :py:meth:`~nwbinspector.checks.time_series.check_regular_timestamps`



.. _best_practice_chunk_data:

Chunk Data
~~~~~~~~~~

Use chunking to optimize reading of large data for your use case.

By default, when using the HDF5 backend, TimeSeries data are stored on disk in column-based ordering.

This means that if the `data` of a TimeSeries has multiple dimensions, then all data from a single timestamp are stored
contiguously on disk, followed by the next timestamp, and so on.

This storage scheme may be optimal for certain uses, such as slicing TimeSeries by time; however, it may be sub-optimal
for other uses, such as reading data from all timestamps for a particular value in the second or third dimension.

This is especially important when writing NWBFiles that are intended to be uploaded to the 
:dandi-archive:`DANDI Archive <>` for storage, sharing, and publication.

For more information about how to enable chunking and compression on your data, consult the 
:pynwb-docs:`PyNWB tutorial <tutorials/advanced_io/h5dataio.html#chunking>` or the
`MatNWB instructions <https://neurodatawithoutborders.github.io/matnwb/tutorials/html/dataPipe.html#2>`_.


.. _best_practice_large_dataset_compression:

Compress Data
~~~~~~~~~~~~~

Data writers can optimize the storage of large data arrays for particular uses by using compression applied to each 
chunk individually.

This is especially important when writing NWBFiles that are intended to be uploaded to the 
:dandi-archive:`DANDI Archive <>` for storage, sharing, and publication.

For more information about how to enable compression on your data, consult the 
:pynwb-docs:`PyNWB tutorial <tutorials/advanced_io/h5dataio.html#compression-and-other-i-o-filters>` or the
`MatNWB instructions <https://neurodatawithoutborders.github.io/matnwb/tutorials/html/dataPipe.html#2>`_

Check function: :ref:`~nwbinspector.checks.nwb_containers.check_large_dataset_compression`
