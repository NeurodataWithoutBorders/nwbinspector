Time Series
===========

Many of the neurodata_types in NWB inherit from the TimeSeries neurodata_type.

When using TimeSeries or any of its descendants, make sure the following are followed.

Dimension Order
~~~~~~~~~~~~~~~

The time dimension always goes first. In TimeSeries.data, the first dimension on the disk is always time.

Keep in mind that the dimensions are reversed in MatNWB, so in memory in MatNWB the time dimension must be last.

In PyNWB the order of the dimensions is the same in memory as on disk, so the time index should be first.


Units of Time
~~~~~~~~~~~~~

Time-related values should always in seconds. This include ```rate``` (if applicable), which should should be in Hz.


Global Time Reference
~~~~~~~~~~~~~~~~~~~~~

```timestamps``` or ```starting_time``` should be in seconds with respect to the global ```timestamps_reference_time``` of the NWBFile.

Subtypes
~~~~~~~~

ElectrialSeries are reserved for neural data. ElectrialSeries holds signal from electrodes positioned in or around the brain that are monitoring neural
activity, and only those electrodes should be in the electrodes table.

Breaks in Continuity
~~~~~~~~~~~~~~~~~~~~
TimeSeries data should be stored as one continuous stream.

Data should be stored in one continuous stream, as it is acquired, not by trial as is often reshaped for analysis.

Data can be trial-aligned on-the-fly using the trials table.

Storing measured data as a continuous stream ensures that other users have access to the inter-trial data, and that we can align the data with whatever window they need.

If you only have data spanning specific segments of time, then only include those timepoints in the data.

One could use timestamps for this, even if there is a constant sampling rate within each segment, and have the timestamps correctly reflect the gaps in the recording.


.. _best_practice_regular_timestamps:

Timestamps vs. Start & Rate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Use timestamps, even if there is a constant sampling rate within each segment, and have the timestamps correctly
reflect the gaps in the recording. Use the TimeSeries.description field to explain how the data was segmented.
If the sampling rate is constant, use rate. TimeSeries allows you to specify time using either timestamps or rate and starting_time (which defaults to 0).
For TimeSeries objects that have a constant sampling rate, rate should be used instead of timestamps. This will ensure that you can use analysis and
visualization tools that rely on a constant sampling rate.

Check function: :ref:`check_regular_timestamps <check_regular_timestamps>`



Unassigned
~~~~~~~~~~

Use chunking to optimize reading of large data for your use case. By default, when using the HDF5 backend, TimeSeries data are stored on disk in C-ordering.
This means that if “data” dataset of a TimeSeries has multiple dimensions, then all data from a single timestamp are stored contiguously on disk, then data
from the next timestamp are stored contiguously. This storage scheme may be optimal for certain uses, such as slicing TimeSeries by time; however, it may be
sub-optimal for other uses, such as reading data from all timestamps for a particular value in the second or third dimension. Data writers can optimize the
storage of large data arrays for particular uses by using chunking and compression. For more information about chunking and compression, consult the PyNWB
documentation and MatNWB documentation.
