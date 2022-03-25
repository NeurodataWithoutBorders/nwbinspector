Optogenetics
============

.. _best_practice_optogenetic_stimulus_site_has_optogenetic_series:

OptogeneticSeries
-----------------

Each ``OptogeneticStimulusSite`` object present in an ``NWBFile`` should
be referenced by at least on ``OptogeneticSeries`` in the same file.

Check function: :py:meth:`~nwbinspector.checks.ogen.check_optogenetic_stimulus_site_has_optogenetic_series`
