HED Annotations
===============

`HED <https://www.hedtags.org/hed-resources/>`_ (Hierarchical Event Descriptors) is a controlled vocabulary for
annotating events and other tabular data. In NWB, HED annotations are stored with the
`ndx-hed <https://github.com/hed-standard/ndx-hed>`_ extension, which adds ``HedTags`` and ``HedValueVector``
columns to any :ref:`hdmf-schema:sec-dynamictable` and a ``HedLabMetaData`` object that records the version of
the HED schema in use. Because the annotations are drawn from a formal vocabulary, they can be validated, and
the NWB Inspector reports each validation error as a separate message.

Validating HED annotations requires the ``ndx-hed`` package, which is not installed by default. Install it with
``pip install nwbinspector[hed]``. Without it, the NWB Inspector will read files that contain HED annotations
but will not validate them.

.. _best_practice_hed_lab_metadata:

Declare the HED Schema Version
------------------------------

A file that contains HED annotations should also contain a ``HedLabMetaData`` object giving the version of the
HED schema that the annotations were written against. The vocabulary changes between versions, so without the
version the annotations cannot be interpreted or validated:

.. code-block:: python

    from ndx_hed import HedLabMetaData

    nwbfile.add_lab_meta_data(HedLabMetaData(hed_schema_version="8.4.0"))

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_lab_metadata_exists`

.. _best_practice_hed_annotations:

Use Valid HED Annotations
-------------------------

Every HED annotation in the file should validate against the declared HED schema. Common errors are tags that
are not in the schema, tags that are misspelled, and value templates that expand into invalid tags once the
value from the column is substituted for the ``#`` placeholder. The NWB Inspector reports the errors found by
the validator that ``ndx-hed`` provides, one message per error, with an error that repeats down a column
collapsed into a single message.

The inspector validates each annotated column of each table on its own, which is what the annotation of that
column means in isolation. It does not perform the assembled validation that ``ndx-hed`` offers, which combines
all the annotations of a row into one HED string and validates the table as a timeline. That form of validation
requires reading the whole table into memory, which the inspector avoids so that it can run on large files and
on files read over a network. Run ``HedNWBValidator.validate_file`` from ``ndx-hed`` directly to get it.

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_annotations_valid`

.. _best_practice_hed_value_vector_meanings_table:

Annotate a MeaningsTable with HedTags, Not HedValueVector
---------------------------------------------------------

A ``MeaningsTable`` assigns a meaning to each individual value of a categorical column, so its HED annotations
are complete HED strings stored in a ``HedTags`` column, one annotation per value. A ``HedValueVector`` is the
opposite construct: a single template annotation with a ``#`` placeholder that each value of a column is
substituted into. A template has no role inside a ``MeaningsTable``, and the ``ndx-hed`` validator rejects
files that place one there.

Check function: :py:meth:`~nwbinspector.checks._hed.check_hed_value_vector_not_in_meanings_table`
