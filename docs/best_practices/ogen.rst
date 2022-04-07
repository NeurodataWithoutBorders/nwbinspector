Optogenetics
============

.. _best_practice_optogenetic_stimulus_site_has_optogenetic_series:

OptogeneticSeries
-----------------

Each :nwb-schema:ref:`sec-OptogeneticStimulusSite` object present in an :nwb-schema:ref:`sec-NWBFile` should
be referenced by at least one :nwb-schema:ref:`sec-OptogeneticSeries` in the same file.

Check function: :py:meth:`~nwbinspector.checks.ogen.check_optogenetic_stimulus_site_has_optogenetic_series`
