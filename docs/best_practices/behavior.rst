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



Sleep States
------------

.. _best_practice_sleep_states_hed:

HED Annotation of Sleep States
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a table holds scored sleep states in a categorical column, such as the ``label`` column of a
:ref:`nwb-schema:sec-TimeIntervals` table of sleep bouts, give each state a `HED <https://www.hedtags.org>`_
(Hierarchical Event Descriptors) annotation in a ``HED`` column of the column's ``MeaningsTable``
(see :ref:`best_practice_meanings_table_includes_all_values`). This makes the states machine-readable across
datasets. The states are tagged with the standard schema's agent states, and sleep stages with the
`SCORE library <https://github.com/hed-standard/hed-schemas/tree/main/library_schemas/score>`_ (prefix ``sc:``):

.. list-table::
   :header-rows: 1

   * - State
     - HED annotation
   * - Waking
     - ``Awake``
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

    # sleep_states is the table of sleep bouts, with the scored state in its "label" column
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
