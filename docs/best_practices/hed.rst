HED Annotations
===============

`HED <https://www.hedtags.org/hed-resources/>`_ (Hierarchical Event Descriptors) is a controlled vocabulary for
annotating events and other tabular data. In NWB, HED annotations are stored with the
`ndx-hed <https://github.com/hed-standard/ndx-hed>`_ extension. It adds three kinds of column to any
:ref:`hdmf-schema:sec-dynamictable`: ``HedTags``, a column named ``HED`` that holds a HED string for each row;
``HedValueVector``, a column of values with a HED template such as ``Age/# s`` that each value is substituted
into; and ``HedDurationVector``, the ``duration`` column of an ``EventsTable`` with such a template. A
categorical column is annotated with a ``HedTags`` column named ``HED`` in its ``MeaningsTable``, which gives the
HED of each value. A ``HedLabMetaData`` object records the version of the HED schema in use and any HED
definitions. Because the annotations are drawn from a formal vocabulary, they can be validated.

Validating HED annotations requires the ``ndx-hed`` package, which is not installed by default. Install it with
``pip install nwbinspector[hed]``. Without it, the NWB Inspector reads files that contain HED annotations and
reports each table that has them as not validated.

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
are not in the schema, references to definitions that do not exist, values that do not fit the template of their
column once substituted for the ``#`` placeholder, and a ``HedValueVector`` placed in a ``MeaningsTable``.

The NWB Inspector validates each table that carries HED with the validator that ``ndx-hed`` provides, and does not
read the tables that carry none. The validator works in stages: the templates, the ``MeaningsTable`` HED, and the
definitions first, then the values of each annotated column, then the ``HED`` column. Once those pass, the HED
of each row is assembled from all of its annotations and validated as a whole, which catches errors such as a
tag that appears both in the ``HED`` column and in the HED of a categorical value. Each stage runs only if the
earlier ones found no errors, so fixing the reported errors can reveal further ones on the next run. Assembling
the rows reads the whole table, which for a table of 100,000 rows takes several seconds.

Each value is validated once, so an error is reported at the first row that holds the value, with the number of
rows that hold it. Errors with the same code in the same column, such as several different words in a column of
numbers, are reported together as a single message that lists the HED strings with the error, the first row of
each, and how many rows hold it.

Warnings of the validator, such as a tag that extends the schema, are reported separately as suggestions. They
are gathered without assembling the rows.

Check functions: :py:meth:`~nwbinspector.checks._hed.check_hed_annotations_valid` and
:py:meth:`~nwbinspector.checks._hed.check_hed_annotations_warnings`
