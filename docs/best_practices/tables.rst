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

It is also encouraged practice for boolean columns to be named ``is_condition`` where ``condition`` is whatever the
positive state of the variable is.

The reason for this practice is two-fold:

(i) It allows for easier user comprehension of the information by intuitively restricting the range of possible values
for the column; a user would otherwise have to extract all the values and calculate the unique set to see that there
are only two values.

(ii) For large amounts of data, it also saves storage space for the data within the HDF5 file by using the minimal
number of bytes per item. This can be especially importance if the repeated values are long strings or float casts of
``1`` and ``0`` (which can take 8 times as much space per item).

An example of a violation of this practice would be for a column of strings with the following values everywhere;

.. code-block:: python

    hit_or_miss_col = ["Hit", "Miss", "Miss", "Hit", ...]

and so on. This should instead become...

.. code-block:: python

    is_hit = [True, False, False, True, ...]


Check function :py:meth:`~nwbinspector.checks.tables.check_column_binary_capability`

.. note::

    If the two unique values in your column are ``float`` types that differ from ``1`` and ``0``, the reported values
    are to be considered as additional contextual information for the column, and this practice does not apply.



Timing Columns
~~~~~~~~~~~~~~

Times are always stored in seconds in NWB. This rule applies to times in :nwb-schema:ref:`sec-TimeSeries`,
:nwb-schema:ref:`sec-TimeIntervals` and across NWB in general. *E.g.*, in :nwb-schema:ref:`sec-TimeIntervals`
objects such as the :nwb-schema:ref:`Trials <sec-groups-intervals-trials>` and
:nwb-schema:ref:`EpochTable <epochs>`, ``start_time`` and ``stop_time`` should both be in seconds with respect to the
``timestamps_reference_time`` of the :nwb-schema:ref:`sec-NWBFile` (which by default is the
``session_start_time``, see :ref:`best_practice_global_time_reference` for more details).

Additional time columns in :nwb-schema:ref:`sec-TimeIntervals` tables, such as the
:nwb-schema:ref:`Trials <sec-groups-intervals-trials>` should have ``_time`` appended as a suffix to the name.
*E.g.*, if you add more times in the :nwb-schema:ref:`Trials <sec-groups-intervals-trials>`, such as a subject
response time, name it ``response_time`` and store the time values in seconds from the ``timestamps_reference_time``
of the :nwb-schema:ref:`sec-NWBFile`, just like ``start_time`` and ``stop_time``.
This convention is used by downstream processing tools. For instance, NWBWidgets uses these times to create peri-stimulus time histograms relating spiking activity to trial events.
See :ref:`best_practice_global_time_reference` for more details.
