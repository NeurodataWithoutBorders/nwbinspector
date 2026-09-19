Miscellaneous
=============


DecompositionSeries
-------------------

:ref:`nwb-schema:sec-DecompositionSeries` stores the product of spectral analysis (e.g., wavelet decomposition, short-time
Fourier transform). The data is 3D (time x channels x frequency bands) and has a ``metric`` field indicating what the
values represent (recommended values: "phase", "amplitude", "power").

.. _best_practice_decomposition_series_unit:

DecompositionSeries Unit
~~~~~~~~~~~~~~~~~~~~~~~~

The unit of a :ref:`nwb-schema:sec-DecompositionSeries` should be appropriate for its metric. When the metric is "phase",
the unit should be "radians" or "degrees". When the metric is "amplitude", the unit should match the unit of the source
signal (e.g., "volts" if the source is an ElectricalSeries). The PyNWB default of "no unit" should be replaced with
the actual unit.

Check function: :py:meth:`~nwbinspector.checks._misc.check_decomposition_series_unit`


.. _best_practice_decomposition_series_source:

DecompositionSeries Source TimeSeries
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A :ref:`nwb-schema:sec-DecompositionSeries` should link to the source TimeSeries that was decomposed via the
``source_timeseries`` field. This provides provenance about the origin of the decomposed signal and enables
validation of the unit field.

Check function: :py:meth:`~nwbinspector.checks._misc.check_decomposition_series_source_timeseries`
