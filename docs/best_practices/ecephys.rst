Extracallular electrophysiology
===============================



Electrodes
----------


.. _best_practice_ecephys_location:

Location
~~~~~~~~

The ``location`` column of the ``ElectrodeTable`` should reflect your best estimate of the recorded
brain area. Different labs have different standards for electrode localization. Some use atlases and coordinate maps to
precisely place an electrode, and use physiological measures to confirm its placement. Others use histology or imaging
processing algorithms to identify regions after-the-fact. You fill this column with localization results from your most
accurate method. For instance, if you target electrodes using physiology, and later use histology to confirm placement,
we would recommend that you add a new column to the electrodes table called 'location_target', set those values to the
original intended target, and alter the values of 'location' to match the histology results.

The ``location`` column of the ``ElectrodeTable`` is required. If you do not know the location of
an electrode, use "unknown".



.. _best_practice_ecephys_ontologies:

Ontologies
~~~~~~~~~~

It is preferable to use established ontologies instead of lab conventions for indicating anatomical region.
We recommend the :allen-brain-map:`Allen Brain Atlas <atlas>` terms for mice, and you may use either the full name or
the abbreviation (do not make up your own terms).



.. _best_practice_ecephys_anatomical_coordinates:

Anatomical Coordinates
~~~~~~~~~~~~~~~~~~~~~~

The ``x``, ``y``, and ``z`` columns of the ``ElectrodeTable`` are for the precise anatomical
coordinates within the Subject. For mice, use the
:allen-brain-map:`Allen Institute Common Coordinate Framework v3 <atlas>`, which follows the convention
(+x = posterior, +y = inferior, +z = subject's right).



.. _best_practice_ecephys_relative_coordinates:

Relative Coordinates
~~~~~~~~~~~~~~~~~~~~

For relative position of an electrode on a probe, use ``rel_x``, ``rel_y``, and ``rel_z`` columns of the
``ElectrodeTable``. These positions will be used by spike sorting software to determine electrodes
that are close enough to share a neuron.



Units Table
-----------

.. _best_practice_negative_spike_times:

Negative Spike Times
~~~~~~~~~~~~~~~~~~~~

All spike times should be greater than zero. Being less than zero implies the spikes are either trial-aligned (and
should therefore be aligned to the ``timestamps_reference_time`` of the :ref:`nwb-schema:sec-NWBFile`) or the
``timestamps_reference_time`` itself is not set to the earliest recording time during the session.

Check function: :py:meth:`~nwbinspector.checks.ecephys.check_negative_spike_times`



.. _best_practice_spike_times_not_in_unobserved_interval:

Observation Intervals
~~~~~~~~~~~~~~~~~~~~~

The ``obs_intervals`` field of the :ref:`nwb-schema:sec-units-src` table is used to indicate periods of time where the underlying electrical signal(s) were not observed. This can happen if the recording site moves away from the unit, or if the recording is stopped. Since the channel is not observed, it is not determinable whether a spike occurred during this time. Therefore, there should not be any identified spike times for units matched to those electrical signal(s) occurring outside of the defined ``obs_intervals``. If this variable is not set, it is assumed that all time is observed.

Check function: :py:meth:`~nwbinspector.checks.ecephys.check_spike_times_not_in_unobserved_interval`



.. _best_practice_ascending_spike_times:

Ascending Spike Times
~~~~~~~~~~~~~~~~~~~~~

All spike times should be sorted in ascending order. If they reset to zero, this can be a sign that spikes are not properly aligned with the ``timestamps_reference_time`` of the :ref:`nwb-schema:sec-NWBFile`.

Check function: :py:meth:`~nwbinspector.checks.ecephys.check_ascending_spike_times`
