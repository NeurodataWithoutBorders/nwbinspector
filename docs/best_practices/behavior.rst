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


.. _best_practice_sleep_states_hed:

HED Annotation of Sleep States
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To make the states machine-readable across datasets, give each label a `HED <https://www.hedtags.org>`_ (Hierarchical Event Descriptors) annotation in a ``HED``
column of the ``MeaningsTable`` for ``label``. The states are tagged with the standard schema's agent states,
and sleep stages with the `SCORE library <https://github.com/hed-standard/hed-schemas/tree/main/library_schemas/score>`_
(prefix ``sc:``):

.. list-table::
   :header-rows: 1

   * - State
     - HED annotation
   * - Waking
     - ``Awake``
   * - Quiet waking
     - ``Awake, Resting``
   * - Drowsiness
     - ``Drowsy``
   * - Non-REM sleep, not divided into stages (as is usual in rodents)
     - ``Asleep``
   * - Non-REM stage 1, 2 or 3
     - ``Asleep, sc:Sleep-stage-N1``, ``Asleep, sc:Sleep-stage-N2`` or ``Asleep, sc:Sleep-stage-N3``
   * - REM sleep
     - ``Asleep, sc:Sleep-stage-REM``

Tag a state only as precisely as it was scored. A non-REM state that was not divided into stages is ``Asleep``,
not a guess at a stage. A state with no fitting tag, such as an intermediate or transitional state, keeps its
meaning in the ``MeaningsTable`` and gets an empty annotation, or ``Asleep`` if it is a kind of sleep.

The file declares both schemas in its ``HedLabMetaData`` (from the
`ndx-hed <https://github.com/hed-standard/ndx-hed>`_ extension):

.. code-block:: python

    from hdmf.common import MeaningsTable
    from ndx_hed import HedLabMetaData, HedTags

    nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version='["8.4.0", "sc:score_2.1.0"]'))

    meanings = MeaningsTable(target=sleep_states["label"])
    meanings.add_column(name="HED", description="HED annotation of each state", col_cls=HedTags)
    meanings.add_row(value="Wake", meaning="waking: high theta/delta ratio and EMG activity", HED="Awake")
    meanings.add_row(
        value="NREM", meaning="non-REM sleep: high delta/theta ratio and very low EMG activity", HED="Asleep"
    )
    meanings.add_row(
        value="REM",
        meaning="REM sleep: high theta/delta ratio and no EMG activity",
        HED="Asleep, sc:Sleep-stage-REM",
    )
    sleep_states.add_meanings_table(meanings)


.. _best_practice_sleep_states_multiple_scorings:

Multiple Scorings
~~~~~~~~~~~~~~~~~

When a session was scored more than once, for example by hand for a publication and later by an automatic method,
store each scoring in its own table (for example ``sleep_states`` and ``sleep_states_auto``). Each table's
description should say which method made it and which scoring the publication used. Do not store only one of them
under a generic name without saying which it is.
