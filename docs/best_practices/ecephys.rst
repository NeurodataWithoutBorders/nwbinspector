Extracallular electrophysiology
===============================



Electrodes
----------


.. _best_practice_ecephys_location:

Location
~~~~~~~~

The 'location' field should reflect your best estimate of the recorded brain area. Different labs have different
standards for electrode localization. Some use atlases and coordinate maps to precisely place an electrode, and use
physiological measures to confirm its placement. Others use histology or imaging processing algorithms to identify
regions after-the-fact. You fill this column with localization results from your most accurate method. For instance,
if you target electrodes using physiology, and later use histology to confirm placement, we would recommend that you
add a new column to the electrodes table called 'location_target', set those values to the original intended target,
and alter the values of 'location' to match the histology results.

The ``location`` column of the electrodes table is required. If you do not know the location of an electrode, use
'unknown'.



.. _best_practice_ecephys_ontologies:

Ontologies
~~~~~~~~~~

It is preferable to use established ontologies instead of lab conventions for indicating anatomical region.
We recommend the :allen-brain-map:`Allen Brain Atlas <atlas>` terms for mice, and you may use either the full name or
the abbreviation (do not make up your own terms).



.. _best_practice_ecephys_anatomical_coordinates:

Anatomical Coordinates
~~~~~~~~~~~~~~~~~~~~~~

The ``x``, ``y``, and ``z`` arguments to the :py:meth:`~pynwb.file.NWBFile.add_electrode` function are for the precise
anatomical coordinates within the Subject. For mice, use the :allen-brain-map:`Allen Institute Common Coordinate
Framework v3 <atlas>`, which follows the convention (+x = posterior, +y = inferior, +z = right).



.. _best_practice_ecephys_relative_coordinates:

Relative Coordinates
~~~~~~~~~~~~~~~~~~~~

For relative position of an electrode on a probe, use ``rel_x``, ``rel_y``, and ``rel_z``. These positions will be used
by spike sorting software to determine electrodes that are close enough to share a neuron.



Units Table
-----------


.. _best_practice_negative_spike_times:

Negative Spike Times
~~~~~~~~~~~~~~~~~~~~

All spike times should be greater than zero. Being less than zero implies the spikes are either trial-aligned (and
should therefore be aligned to the global :py:attr:`~pynwb.file.NWBFile.timestamp_reference_time`) or the
:py:attr:`~pynwb.file.NWBFile.timestamp_reference_time` is not set to agree with the
:py:attr:`~pynwb.file.NWBFile.session_start_time`. In either case the spike times (and all other temporal data) should
be aligned to the earliest recorded timestamp in the file.

Check function: :py:meth:`~nwbinspector.checks.ecephys.check_negative_spike_times`
