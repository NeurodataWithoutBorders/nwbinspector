Tables
======

The :nwb-schema:ref:`dynamictable` data type allows you to define custom columns, which offer a high
degree of flexibility.



.. _best_practice_single_row:

Tables With Only a Single Row
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

It is not common to save a table with only a single row entry. Consider other ``neurodata_types``, such as a one-dimensional :nwb-schema:ref:`sec-TimeSeries` or any of its subtypes.

Check function: :py:meth:`~nwbinspector.checks.tables.check_single_row`



.. _best_practice_dynamic_table_region_data_validity:

Table Region Data
~~~~~~~~~~~~~~~~~

Store data with long columns rather than long rows. When constructing dynamic tables, keep in mind that the data is
stored by column, so it will be inefficient to store data in a table with many columns.

Check function :py:meth:`~nwbinspector.checks.tables.check_dynamic_table_region_data_validity`



.. _best_practice_column_binary_capability:

Boolean Columns
~~~~~~~~~~~~~~~

Use boolean values where appropriate. Although boolean values (``True``/``False``) are not used in the core schema,
they are a supported data type, and we encourage the use of :nwb-schema:ref:`dynamictable` columns with boolean
values. For instance, boolean values would be appropriate for a correct custom column to the trials table.

Check function :py:meth:`~nwbinspector.checks.tables.check_column_binary_capability`



Timing Columns
~~~~~~~~~~~~~~

Times are always stored in seconds in NWB. This rule applies to times in :nwb-schema:ref:`sec-TimeSeries`,
:nwb-schema:ref:`sec-TimeIntervals` and across NWB in general. *E.g.*, in :nwb-schema:ref:`sec-TimeIntervals`
objects such as the :nwb-schema:ref:`TrialsTable <sec-groups-intervals-trials>` and
:nwb-schema:ref:`EpochTable <epochs>`, ``start_time`` and ``stop_time`` should both be in seconds with respect to the
``timestamps_reference_time`` of the :nwb-schema:ref:`sec-NWBFile` (which by default is also set to the
``session_start_time``, see :ref:`best_practice_global_time_reference` for more details).

Additional time columns in :nwb-schema:ref:`sec-TimeIntervals` tables, such as the
:nwb-schema:ref:`TrialsTable <sec-groups-intervals-trials>` should have ``_time`` appended as a suffix to the name.
*E.g.*, if you add more times in the :nwb-schema:ref:`TrialsTable <sec-groups-intervals-trials>`, such as a subject
response time, name it ``response_time`` and store the time values in seconds from the ``timestamps_reference_time``
of the :nwb-schema:ref:`sec-NWBFile`, just like ``start_time`` and ``stop_time``.
See :ref:`best_practice_global_time_reference` for more details.
