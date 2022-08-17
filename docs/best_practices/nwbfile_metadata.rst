NWBFile Metadata
================

An :nwb-schema:ref:`sec-NWBFile` object generally contains data from a single experimental session.



File Organization
-----------------


.. _best_practice_global_time_reference:

Global Date and Time Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

An :nwb-schema:ref:`sec-NWBFile` can have two primary time references. The global date and time reference for all
objects in the :nwb-schema:ref:`sec-NWBFile` is the ``timestamps_reference_time``. By default, this is set to the
``session_start_time``, but when writing multiple NWBFiles that are all designed to align to the same time reference,
the ``timestamp_reference_time`` used across all of the NWBFiles may be set separately from the ``session_start_time``.

All time-related data in the NWBFile should be synchronized to the ``timestamps_reference_time`` so that future users
are able to understand the timing of all events contained within the NWBFile.

Given the importance of this field within an :nwb-schema:ref:`sec-NWBFile`, is it critical that it be set to a proper
value. Default values should generally not be used for this field. If the true date is unknown, use your
best guess. If the exact start time is unknown, then it is fine to simply set it to midnight on that date.


Check functions: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_session_start_time_old_date`,
:py:meth:`~nwbinspector.checks.nwbfile_metadata.check_session_start_time_future_date`,



.. _best_practice_acquisition_and_processing:

Acquisition & Processing
~~~~~~~~~~~~~~~~~~~~~~~~

The 'acquisition' group is specifically for time series measurements that are acquired from an acquisition system,
*e.g.*, an :nwb-schema:ref:`sec-ElectricalSeries` with the voltages from the recording systems or the raw output of
any other environmental sensors.

The 'processing' modules are for intermediate data, *e.g.*, if you derive the position of the animal from sensors or
video tracking, that would go in ``/processing/behavior/Position/SpatialSeries``. An LFP signal that is a downsampled
version of the acquired data would go in ``/processing/ecephys/LFP/ElectricalSeries``.

It may not always be 100% clear whether data is acquired or derived, so in those cases you should just use your best
judgement.



.. _best_practice_processing_module_name:

Processing Module Names
~~~~~~~~~~~~~~~~~~~~~~~

The name of any given processing module should be chosen from the following types: "ophys", "ecephys", "icephys",
"behavior", "ogen", "retinotopy", or "misc". This helps standardize navigation of NWBFiles generated from labs and
modalities. It also helps distinguish components of a given experiment, such as decoupling the intermediate data from
neural acquisition systems from behavioral ones.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_processing_module_name`



File Metadata
-------------


.. _best_practice_file_id:

File Identifiers
~~~~~~~~~~~~~~~~

An :nwb-schema:ref:`sec-NWBFile` has two distinct places for identifiers: ``NWBFile.session_id`` and ``identifier``.

The ``session_id`` field marks unique experimental sessions. The ``session_id`` should have a one-to-one relationship
with a recording session. Sometimes you may find yourself having multiple NWBFiles that correspond to the same session.
This can happen, for instance, if you separate out processing steps across multiple files or if you want to compare
different processing outputs. In this case, the ``session_id`` should be the same for each file. Each lab should follow
a standard structure for their own naming schemes so that sessions are unique within the lab and the IDs are easily
human-readable.

The ``identifier`` tag should be a globally unique value for the :nwb-schema:ref:`sec-NWBFile`. Two different NWBFiles
from the same session should have different ``identifier`` values if they differ in any way. It is recommended that you
use a well-established algorithmic generator such as ``uuid`` to ensure uniqueness. ``uuid`` can be
:uuid:`used in PyNWB <>`, and MatNWB will automatically set the field using ``java.util.UUID.randomUUID().toString()``.
The ``identifier`` field does not need to be easily human-readable.



.. _best_practice_experimenter:

Experimenter
~~~~~~~~~~~~

The ``experimenter`` field of an :nwb-schema:ref:`sec-NWBFile` should be specified. This allows metadata collection
programs, such as those on the :dandi-archive:`DANDI archive <>` to easily scan NWBFiles to more easily link individual
authors to publications and external IDs, such as :orcid:`ORCID`.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_experimenter`



.. _best_practice_experiment_description:

Experiment Description
~~~~~~~~~~~~~~~~~~~~~~

The ``experiment_description`` field of an :nwb-schema:ref:`sec-NWBFile` should be specified. This helps provide
context for understanding the contents of the file.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_experiment_description`



.. _best_practice_institution:

Institution
~~~~~~~~~~~

The ``institution`` field should be specified. This allows metadata collection programs, such as those on the
:dandi-archive:`DANDI archive <>` to easily scan NWBFiles to deliver summary statistics.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_institution`



.. _best_practice_keywords:

Keywords
~~~~~~~~

The ``keywords`` field should be specified. This allows metadata collection programs, such as those on the
:dandi-archive:`DANDI archive <>` to easily scan NWBFiles to enhance keyword-based search functionality. Try to think
of what combination of words might make your file(s) unique or descriptive to help users trying to search for it. This
could include the general modality or approach, the general region of cortex you wanted to study, or the type of neural
data properties you were examining. Some examples are``"neuropixel"``, ``"hippocampus"``, ``"lateral septum"``,
``"waveforms"``, ``"cell types"``, ``"granule cells"``, etc.

If you are unsure of what keywords to use, try searching existing datasets on the :dandi-archive:`DANDI archive <>` for
an approach similar to yours and try to align your own keywords to that while adding a couple that make your file(s)
distinguishable.



.. _best_practice_doi_publications:

Link to DOI Publications
~~~~~~~~~~~~~~~~~~~~~~~~

The ``related_publications`` field does not need to be specified, but if it is it should be an explicit DOI link, either
of the form ``'doi: ###'`` or as an external link of the form ``'http://dx.doi.org/###"'`` or `'https://doi.org/###'``.
This allows metadata collection programs, such as those on the :dandi-archive:`DANDI archive <>` to easily form direct
hyperlinks to the publications.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_doi_publications`



.. _best_practice_subject_exists:

Subject
-------

It is recommended to always include as many details about the experimental subject as possible. If the data is
simulated, a simple ID of "simulated_subject" would be sufficient.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_exists`



.. _best_practice_subject_id_exists:

ID
~~

A ``subject_id`` is required for upload to the :dandi-archive:`DANDI archive <>`. Even if the goal of a given NWBFile is
not intended for DANDI upload, if the :nwb-schema:ref:`sec-Subject` is specified at all it should be given a
``subject_id`` for reference.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_id_exists`



.. _best_practice_subject_sex:

Sex
~~~

The ``sex`` of the :nwb-schema:ref:`sec-Subject` should be specified as a single upper-case character among the
following four possibilities: "M" (male), "F" (female), "U" (unknown), or "O" (other, for asexual species).

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_sex`



.. _best_practice_subject_species:

Species
~~~~~~~

The ``species`` of a :nwb-schema:ref:`sec-Subject` should be set to the proper
:wikipedia:`Latin binomial <Binomial_nomenclature>`. *E.g.*, a rat would be "Rattus norvegicus".

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_species`



Strain
~~~~~~~

The ``strain`` of a :nwb-schema:ref:`sec-Subject` should be set to further indicate the subspecies or breed or common genetic modification. *E.g.*, common strains for species "Rattus norvegicus" might include "Long Evans", "Sprague-Dawley", "Wistar", or "C57BL/6". If no specific strain is used, then simply indicate "Wild Type".



.. _best_practice_subject_age:

Age
~~~

The ``age`` of a :nwb-schema:ref:`sec-Subject` should use the :wikipedia:`ISO 8601 Duration <ISO_8601#Durations>`
format. For instance indicating an age of 90 days would be 'P90D'. It is not necessary to include both ``age`` and
``date_of_birth``, but at least one of them is required by the DANDI Archive and recommended in general.

If the precise age is unknown, an age range can be given by "[lower bound]/[upper bound]" e.g. "P10D/P20D" would mean
that the age is in between 10 and 20 days. If only the lower or upper bound is known, "**" can be used to indicate a
missing bound. For instance, "P90Y/" would indicate that the age is 90 years or older.

Check function: :py:meth:`~nwbinspector.checks.nwbfile_metadata.check_subject_age`



.. _best_practice_subject_dob:

Date of Birth
~~~~~~~~~~~~~

The ``date_of_birth`` of a :nwb-schema:ref:`sec-Subject` should use the :wikipedia:`ISO 8601 <ISO_8601>` format. For
instance, indicating 30 minutes after noon on April 5th, 2007 would be "2007-04-05T12:30". It is not necessary to
include both ``age`` and ``date_of_birth``, but at least one of them is recommended.
