Tables
======

The DynamicTable data type that NWB uses allows you to define custom columns, which offer a high degree of flexibility.



.. _best_practice_dynamic_table_region_data_validity:

Unassigned
~~~~~~~~~~

Store data with long columns rather than long rows. When constructing dynamic tables, keep in mind that the data is stored by column, so it will be
inefficient to store data in a table with many columns.
bools

Check function :ref:`check_column_binary_capability <check_column_binary_capability>`
:py:func:`nwbinspector.checks.table.check_column_binary_capability`



Use boolean values where appropriate. Although boolean values (True/False) are not used in the core schema, they are a supported data type, and we
encourage the use of DynamicTable columns with boolean values. For instance, boolean values would be appropriate for a correct custom column to the trials table.
times

Times are always stored in seconds in NWB. This rule applies to times in TimeSeries, TimeIntervals and across NWB:N in general. E.g., in TimeInterval
objects such as the trials and epochs table, start_time and stop_time should both be in seconds with respect to the timestamps_reference_time (which by
default is set to the session_start_time).
Additional time columns in TimeInterval tables (e.g., trials) should have _time as name suffix. E.g., if you add more times in the trials table, for
instance a subject response time, name it with _time at the end (e.g. response_time) and store the time values in seconds from the timestamps_reference_time,
just like start_time and stop_time.

Set the timestamps_reference_time if you need to use a different reference time. Rather than relative times, it can in practice be useful to use a common
global reference time across files (e.g., Posix time). To do so, NWB:N allows users to set the timestamps_reference_time which serves as reference for all
timestamps in a file. By default, timestamp_reference_time is usually set to the session_start_time to use relative times.
electrodes: ‘location’
