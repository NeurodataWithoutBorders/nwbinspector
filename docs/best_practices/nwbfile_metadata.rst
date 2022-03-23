NWBFile Metadata
================

An NWBFile object generally contains data from a single experimental session.



File Organization
-----------------


.. _best_practice_global_time_reference:

Global Time Reference
~~~~~~~~~~~~~~~~~~~~~

An NWBFile can have two primary time references. The global time reference for all objects in the NWBFile is the
:py:attr:`~pynwb.file.NWBFile.timestamps_reference_time`. By default, this is also set to the
:py:attr:`~pynwb.file.NWBFile.session_start_time`, but when writing multiple NWBFiles that are all designed to align
to the same time reference, the :py:attr:`~pynwb.file.NWBFile.session_start_time` may be set separately from the
explicitly set common :py:attr:`~pynwb.file.NWBFile.timestamps_reference_time` used across all of the NWBFiles.

All time-related data in the NWBFile should be synchronized to the
:py:attr:`~pynwb.file.NWBFile.timestamps_reference_time` so that future users are able to understand the timing of all
events contained within the NWBFile.



.. _best_practice_acquisition_and_processing:

Acquisition & Processing
~~~~~~~~~~~~~~~~~~~~~~~~

The 'acquisition' group is specifically for time series measurements that are acquired from an acquisition system,
*e.g.*, an :py:class:`~pynwb.ecephys.ElectricalSeries` with the voltages from the recording systems or the raw output of
any other environmental sensors.

The 'processing' modules are for intermediate data, *e.g.*, if you derive the position of the animal from sensors or
video tracking, that would go in ``/processing/behavior/Position/SpatialSeries``. An LFP signal that is a downsampled
version of the acquired data would go in ``/processing/ecephys/LFP/ElectricalSeries``.

It may not always be 100% clear whether data is acquired or derived, so in those cases you should just use your best
judgement.



.. _best_practice_file_id:

File Identifiers
~~~~~~~~~~~~~~~~

NWBFile has two distinct places for identifiers: :py:attr:`~pynwb.file.NWBFile.session_id` and
:py:attr:`~pynwb.file.NWBFile.identifier`.

The :py:attr:`~pynwb.file.NWBFile.session_id` field marks unique experimental sessions. The
:py:attr:`~pynwb.file.NWBFile.session_id` should have a one-to-one relationship with a recording session. Sometimes you
may find yourself having multiple NWBFiles that correspond to the same session. This can happen, for instance, if you
separate out processing steps across multiple files or if you want to compare different processing outputs. In this
case, the :py:attr:`~pynwb.file.NWBFile.session_id` should be the same for each file. Each lab should follow a standard
structure for their own naming schemes so that sessions are unique within the lab and the IDs are easily human-readable.

The :py:attr:`~pynwb.file.NWBFile.identifier` tag should be a globally unique value for the
:py:class:`~pynwb.file.NWBFile`. Two different NWBFiles from the same session should have different
:py:attr:`~pynwb.file.NWBFile.identifier` values if they differ in any way. It is recommended that you use a
well-established algorithmic generator such as :uuid:`uuid <>` (for PyNWB) or ?? (for MatNWB) to ensure uniqueness.
The :py:attr:`~pynwb.file.NWBFile.identifier` does not need to be easily human-readable.



.. _best_practice_subject_exists:

Subject
-------

It is recommended to always include as many details about the experimental subject as possible. If the data is
simulated, a simple ID of "simulated_subject" would be sufficient.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_exists`



.. _best_practice_subject_id_exists:

ID
~~

A Subject ID is required for upload to the :dandi-archive:`DANDI archive <>`. Even if the goal of a given NWBFile is
not intended for DANDI upload, if the :py:class:`~pynwb.file.Subject` is specified at all it should be given a
:py:attr:`~pynwb.file.Subject.subject_id` for reference.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_id_exists`



.. _best_practice_subject_sex:

Sex
~~~

The Subject's :py:attr:`~pynwb.file.Subject.sex` should be specified as a single upper-case character among the
following four possibilities: "M" (male), "F" (female), "U" (unknown), or "O" (other, for asexual species).

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_sex`



.. _best_practice_subject_species:

Species
~~~~~~~

The Subject's species should be set to the proper :wikipedia:`Latin binomial <Binomial_nomenclature>`. *E.g.*, a rat
would be "Rattus norvegicus". Specific subspecies may be further specified by a dash, *e.g.*,
"Rattus norvegicus - Long Evans".

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_species`



.. _best_practice_subject_age:

Age
~~~

The age parameter of Subject should use the :wikipedia:`ISO 8601 Duration <ISO_8601#Durations>` format.
For instance indicating an age of 90 days would be 'P90D'.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_age`



.. _best_practice_subject_dob:

Date of Birth
~~~~~~~~~~~~~

The age parameter of Subject should use the :wikipedia:`ISO 8601 <ISO_8601>` format.
For instance, indicating 30 minutes after noon on April 5th, 2007 would be "2007-04-05T12:30".
