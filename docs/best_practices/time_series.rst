Time Series
===========

When using :ref:`nwb-schema:sec-TimeSeries` or any subtype
(*e.g.*, :ref:`nwb-schema:sec-ElectricalSeries`, :ref:`nwb-schema:sec-SpatialSeries`,
:ref:`nwb-schema:sec-ImageSeries`, etc.) please ensure the following practices are followed.




.. _best_practice_data_orientation:

Data Orientation
~~~~~~~~~~~~~~~~

For the ``data`` field of :ref:`nwb-schema:sec-TimeSeries`, the first dimension of the array should always be time.

Keep in mind that the dimensions are reversed in MatNWB, so in memory in MatNWB the time dimension must be last.

In PyNWB the order of the dimensions is the same in memory as on disk, so the time index should be first.

Check functions: :py:meth:`~nwbinspector.checks._time_series.check_data_orientation` and
:py:meth:`~nwbinspector.checks._time_series.check_timestamps_match_first_dimension`



.. _best_practice_unit_of_measurement:

Units of Measurement
~~~~~~~~~~~~~~~~~~~~

Time-related values should always be in seconds. This includes ``rate`` (if applicable), which should be in Hz.

Every :ref:`nwb-schema:sec-TimeSeries` instance has ``unit`` as an attribute, which is meant to indicate the unit of
measurement for that data, using the appropriate type from the
:wikipedia:`International System of Units (SI) <International_System_of_Units>`.

A common mistake is to provide timestamps in milliseconds or microseconds instead of seconds, which results in
unusually long durations (e.g., appearing to span years instead of hours). Similarly, providing the sampling period
(time between samples) instead of the rate (frequency in Hz) leads to suspiciously low rate values.

The sampling rate and timestamps of a series can also be compared with the rest of the file. A series whose stated
rate is the reciprocal of another rate in the file, or whose duration at the stated rate is far longer than the
session while the reciprocal would fit it, most likely holds a sampling period. Timestamps that end far past the rest
of the file, but would fit it if divided by 1e3, 1e6 or 1e9, are most likely in milliseconds, microseconds or
nanoseconds. Voltage and current recordings
should have a rate between 10 Hz and 1 MHz. Series with the same number of samples usually share a clock and should
cover the same duration. A series that runs far past every other series of the file is reported as a suggestion,
since the check cannot tell which side is wrong.

Check functions: :py:meth:`~nwbinspector.checks._time_series.check_missing_unit`,
:py:meth:`~nwbinspector.checks._time_series.check_time_series_duration`,
:py:meth:`~nwbinspector.checks._time_series.check_rate_not_below_threshold`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_rate_is_not_sampling_period`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_timestamps_time_scale`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_rate_in_plausible_range`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_equal_length_series_have_equal_duration`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_series_ends_within_session`



.. _best_practice_time_series_global_time_reference:

Time Series: Time References
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``timestamps`` or ``rate`` of a :ref:`nwb-schema:sec-TimeSeries` should be in seconds with respect to
the global ``timestamps_reference_time`` of the :ref:`nwb-schema:NWBFile <sec-NWBFile>`.
A ``starting_time`` or first timestamp equal to the Unix time of ``timestamps_reference_time`` means that absolute
times were written where relative times were expected. If absolute Unix times are intended, set
``timestamps_reference_time`` to the Unix epoch. A ``starting_time`` of NaN leaves the timing of the series unknown.

Check functions: :py:meth:`~nwbinspector.checks._sampling_rate.check_starting_time_is_not_absolute`,
:py:meth:`~nwbinspector.checks._sampling_rate.check_starting_time_is_finite`



.. _best_practice_time_series_subtypes:

Subtypes
~~~~~~~~

:ref:`nwb-schema:sec-ElectricalSeries` are reserved for neural data. An
:ref:`nwb-schema:sec-ElectricalSeries` holds signal from electrodes positioned in or around the
brain that are monitoring neural activity, and only those electrodes should be in the ``ElectrodeTable``.

For non-neural electrodes that still may store and report raw values in Volts, simply use a general
:ref:`nwb-schema:sec-TimeSeries` object with ``units`` set to "Volts".



.. _best_practice_timestamps_ascending:

Breaks in Continuity
~~~~~~~~~~~~~~~~~~~~
The ``data`` field of :ref:`nwb-schema:sec-TimeSeries` should generally be stored as one continuous stream
as it was acquired, not by trial as is often reshaped for analysis.

Data can be trial-aligned on-the-fly using the ``TrialTable``.

Storing measured data as a continuous stream ensures that other users have access to the inter-trial data, and that we
can align the data within any specifiable window.

If you only have data spanning specific segments of time, then only include those timepoints in the data, see
:ref:`best_practice_regular_timestamps` for more information.

A primary implication is that the values in :ref:`nwb-schema:TimeSeries.timestamps <sec-TimeSeries>`, as well as the
corresponding ordering of their indices in the :ref:`nwb-schema:TimeSeries.data <sec-TimeSeries>` array, should always
be strictly increasing.

Check function: :py:meth:`~nwbinspector.checks._time_series.check_timestamps_ascending`



.. _best_practice_timestamps_without_nans:

Timestamps without NaNs
~~~~~~~~~~~~~~~~~~~~~~~

The ``timestamps`` field of a :ref:`nwb-schema:sec-TimeSeries` should not contain ``NaN`` values, as this can lead to
ambiguity in time references and potential issues in downstream analyses.

Ensure that all timestamps are valid numerical values. If gaps in time need to be represented, consider segmenting the
data into separate :ref:`nwb-schema:sec-TimeSeries` objects with appropriate ``starting_time`` or use the ``timestamps``
vector to explicitly represent time gaps.

Check function: :py:meth:`~nwbinspector.checks._time_series.check_timestamps_without_nans`




.. _best_practice_regular_timestamps:

Timestamps vs. Start & Rate
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:ref:`nwb-schema:sec-TimeSeries` allows you to specify time using either ``timestamps`` or ``rate``
together with ``starting_time`` (which defaults to 0). If the sampling rate is constant, then specify the ``rate`` and
``starting_time`` instead of writing the full ``timestamps`` vector.

For segmented data, refer to the section covering :ref:`best_practice_timestamps_ascending`;

    1. If the sampling rate is constant within each segment, each segment can be written as a separate
    :ref:`nwb-schema:sec-TimeSeries` with the ``starting_time`` incremented appropriately.

    2. Even if the sampling rate is constant within each segment, a single :ref:`nwb-schema:sec-TimeSeries` can be
    written using the ``timestamps`` vector to appropriately indicate the gaps between segments.

Check function: :py:meth:`~nwbinspector.checks._time_series.check_regular_timestamps`


.. _best_practice_avoid_negative_timestamps:

Avoid Negative Timestamps
~~~~~~~~~~~~~~~~~~~~~~~~~

When writing :ref:`nwb-schema:sec-TimeSeries` data, avoid using negative timestamps.

All timestamps in the NWBFile are written with respect to a global reference point (either ``timestamps_reference_time`` or ``session_start_time``).

While negative timestamps are technically valid, they might introduce unnecessary complications for future users of the file.
In most cases, negative timestamps may be indicative of an alignment error or a problem with the source data.
As much as possible, re-align the session start time so that all timestamps are positive and correctly referenced to either ``timestamps_reference_time`` or ``session_start_time``.
See :ref:`best_practice_global_time_reference` for more details.

Check function: :py:meth:`~nwbinspector.checks._time_series.check_timestamp_of_the_first_sample_is_not_negative`

.. _best_practice_resolution:

Unknown Resolution
~~~~~~~~~~~~~~~~~~

If the ``resolution`` of a :ref:`nwb-schema:sec-TimeSeries` is unknown, use ``-1.0`` or ``NaN`` to indicate this.

Check function: :py::meth:`~nwbinspector.checks._time_series.check_resolution`



.. _best_practice_non_zero_rate:

Zero Rate
~~~~~~~~~

If the ``data`` field of :ref:`nwb-schema:sec-TimeSeries` has more than one frame, and according to :ref:`best_practice_data_orientation` this axis ought to be time, then the ``rate`` field should not be ``0.0``.

Check function: :py::meth:`~nwbinspector.checks._time_series.check_rate_is_not_zero`



. _best_practice_positive_rate:

Positive Rate
~~~~~~~~~~~~~

The ``rate`` field of :ref:`nwb-schema:sec-TimeSeries` must be positive when specified. Negative sampling rates are not physically meaningful and indicate an error in the data.

Check function: :py::meth:`~nwbinspector.checks._time_series.check_rate_is_positive`
