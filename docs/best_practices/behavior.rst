Behavior
========


SpatialSeries
-------------

:ref:`nwb-schema:sec-SpatialSeries` objects are specifically for the position (angular or translational) of a Subject over time. Related data such as velocity and acceleration should be placed in a different neurodata object.

.. _best_practice_spatial_series_dimensionality:

SpatialSeries Dimensionality
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:ref:`nwb-schema:sec-SpatialSeries` should have 1 column (x), 2 columns (x, y), or 3 columns (x, y, z).

Check function: :py:meth:`~nwbinspector.checks._behavior.check_spatial_series_dims`


.. _best_practice_spatial_series_units:

SpatialSeries Units
~~~~~~~~~~~~~~~~~~~

When a :ref:`nwb-schema:sec-SpatialSeries` is in a :ref:`nwb-schema:sec-CompassDirection`, the units should either be
"degrees" or "radians".

Check function: :py:meth:`~nwbinspector.checks._behavior.check_compass_direction_unit`


.. _best_practice_spatial_series_general_units:

SpatialSeries General Units
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :ref:`nwb-schema:sec-SpatialSeries` that is not inside a :ref:`nwb-schema:sec-CompassDirection` should have a unit from
the following recognized set: "meters", "centimeters", "millimeters", "micrometers", "degrees", "radians", "pixels",
or "n.a." (not available) as a placeholder when the unit is not known.
These follow the PyNWB convention of full SI words in plural form.

Check function: :py:meth:`~nwbinspector.checks._behavior.check_spatial_series_unit`


.. _best_practice_spatial_series_values:

SpatialSeries Data Values
~~~~~~~~~~~~~~~~~~~~~~~~~

When a :ref:`nwb-schema:sec-SpatialSeries` has units "radians", it should have data values between -2π and 2π. When a
:ref:`nwb-schema:sec-SpatialSeries` has units "degrees", it should have data values between -360 and 360.

Check functions: :py:meth:`~nwbinspector.checks.behavior.check_spatial_series_radians_magnitude`,
:py:meth:`~nwbinspector.checks._behavior.check_spatial_series_degrees_magnitude`


Sleep and Brain States
----------------------

Sleep stages and other scored brain or behavioral states (such as active and quiet waking) are annotations of
periods of time. Store them as intervals rather than as a sampled series of state codes.

.. _best_practice_sleep_states_as_intervals:

Sleep States as Intervals
~~~~~~~~~~~~~~~~~~~~~~~~~

Store scored states in a :ref:`nwb-schema:sec-TimeIntervals` table in the ``behavior``
:ref:`nwb-schema:sec-ProcessingModule`, named for what it holds, such as ``sleep_states``. Each row is one bout,
with its ``start_time`` and ``stop_time`` in seconds on the session's clock and the state in a text column named
``label``. Rows should be in time order and should not overlap. Leave periods that were not scored out of the table
rather than giving them a state.

Do not put the states in the ``epochs`` table, which is for the epochs of the experiment (for example sleep before a
task, the task, and sleep after it), or in the trials table. Do not store them as a :ref:`nwb-schema:sec-TimeSeries`
of integer codes. Integer codes need a separate key to be read, and per-sample values make the bouts hard to find.

.. code-block:: python

    from pynwb.epoch import TimeIntervals

    sleep_states = TimeIntervals(
        name="sleep_states",
        description=(
            "Sleep states scored by hand by the experimenter with TheStateEditor in 4 s windows, from the "
            "theta/delta ratio of the hippocampal LFP and the EMG. Periods of the recording that were not "
            "scored are not in the table."
        ),
    )
    sleep_states.add_column(name="label", description="the scored state: Wake, NREM or REM")
    sleep_states.add_row(start_time=0.0, stop_time=120.5, label="Wake")
    sleep_states.add_row(start_time=120.5, stop_time=842.0, label="NREM")

    behavior_module = nwbfile.create_processing_module(name="behavior", description="behavioral data")
    behavior_module.add(sleep_states)


.. _best_practice_sleep_states_description:

Sleep Scoring Method
~~~~~~~~~~~~~~~~~~~~

The description of a sleep-state table should say how the states were scored, because the same recording can give
different states under different methods:

* manual or automatic scoring, and the person or the software and its version;
* the signals the scoring used, for example the LFP or EEG spectrum, the EMG, an accelerometer or video;
* the scoring window and any minimum bout length.

The meaning of each label should be recorded as well, for example "NREM: high delta/theta ratio and very low EMG
activity". A ``MeaningsTable`` for the ``label`` column holds these definitions
(see :ref:`best_practice_meanings_table_includes_all_values`). Where the scoring distinguishes quiet from active
waking, or splits non-REM sleep into stages, keep those labels instead of merging them into broader ones.


.. _best_practice_sleep_states_multiple_scorings:

Multiple Scorings
~~~~~~~~~~~~~~~~~

When a session was scored more than once, for example by hand for a publication and later by an automatic method,
store each scoring in its own table (for example ``sleep_states`` and ``sleep_states_auto``). Each table's
description should say which method made it and which scoring the publication used. Do not store only one of them
under a generic name without saying which it is.
