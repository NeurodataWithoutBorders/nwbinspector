Behavior
========


SpatialSeries
-------------

.. _best_practice_spatial_series_dimensionality:

Dimensionality
~~~~~~~~~~~~~~

:ref:`nwb-schema:sec-SpatialSeries` should have 1 column (x), 2 columns (x, y), or 3 columns (x, y, z).

.. _best_practice_spatial_series_units:

Units
~~~~~

When a :ref:`nwb-schema:sec-SpatialSeries` is in a :ref:`nwb-schema:sec-CompassDirection`, the units should either be
"degrees" or "radians".

.. _best_practice_spatial_series_values:

Values
~~~~~~

When a :ref:`nwb-schema:sec-SpatialSeries` has units "radians", it should have data values between -2π and 2π. When a
:ref:`nwb-schema:sec-SpatialSeries` has units "degrees", it should have data values between -360 and 360.
