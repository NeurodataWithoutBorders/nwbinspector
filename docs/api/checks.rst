Check Functions
===============

.. automodule:: nwbinspector
    :members:
    :no-undoc-members:

.. toctree::
    :maxdepth: 4

NWBFile Metadata
----------------
.. automodule:: nwbinspector.checks.nwbfile_metadata

NWB Containers
--------------
.. automodule:: nwbinspector.checks.nwb_containers

Time Series
-----------

Check functions that can apply to any descendant of DynamicTable.

.. _check_regular_timestamps:
.. autofunction:: nwbinspector.checks.time_series.check_regular_timestamps
Best Practice: :ref:`best_practice_regular_timestamps`

.. _check_data_orientation:
.. autofunction:: nwbinspector.checks.time_series.check_data_orientation

.. _check_timestamps_match_first_dimension:
.. autofunction:: nwbinspector.checks.time_series.check_timestamps_match_first_dimension

.. _check_timestamps_ascending:
.. autofunction:: nwbinspector.checks.time_series.check_timestamps_ascending

Tables
------
.. automodule:: nwbinspector.checks.tables

Intracellular Electrophysiology (icephys)
-----------------------------------------
.. automodule:: nwbinspector.checks.icephys

Extracellular Electrophysiology (ecephys)
-----------------------------------------
.. automodule:: nwbinspector.checks.ecephys

Optical Electrophysiology (ophys)
---------------------------------
.. automodule:: nwbinspector.checks.ophys
