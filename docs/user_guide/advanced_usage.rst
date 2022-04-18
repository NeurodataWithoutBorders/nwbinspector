Using the Library: Advanced
===========================

This is a collection of tutorials illustrating some of the more advanced uses of the NWBInspector



Yielding and Iterating
----------------------

Both the :py:class:`~nwbinspector.nwbinspector.inspect_all` and :py:class:`~nwbinspector.nwbinspector.inspect_nwb`
functions return generators. That is, they do not actually run any checks on any NWBFile until the user
performs an iteration command on them. The simplest way of doing this is to cast the generator as a ``list``,
*i.e.*, ``list(inspect_nwb(...))`` which will automatically complete all checks.

However, if a user chooses, they can harness these generators in more sophisticated ways. If you want to stop the
checks early, the following will run the inspectors until the first
:py:class:`~nwbinspector.register_checks.InspectorMessage` is returned:

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    first_message = next(results_generator)

This will return either the first :py:class:`~nwbinspector.register_checks.InspectorMessage`, or it will raise a
``StopIteration`` error. This error can be caught in the following manner

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    try:
        first_message = next(results_generator)
    except StopIteration:
        print("There are no messages!")

Of course, the generator can be treated like any other iterable as well, such as with :code:`for` loops

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    for message in results_generator:
        print(message)


Running on a DANDISets (ros3)
-----------------------------

It is a common use case to want to inspect and review entire datasets of NWBFiles that have already been
uploaded to the :dandi-archive:`DANDI Archive <>`. While one could technically just download the DANDISet and
use the NWBInspector as normal, there is another, less expensive possibility in terms of bandwith. This is especially
useful when the underlying dataset is quite large and thus impractical to download - some DANDISets can even be on the
TB scale!

The general tutorial for using the :code:`ros3` driver can be found :ros3-tutorial:`here <>`. This driver can be passed
directly into our core inspection functions, and the ``path`` or ``nwbfile_path`` arguments in this case become the
S3 path on the DANDI archive. Resolution of these paths can be performed via the following code

.. code-block:: python

    from dandi.dandiapi import DandiAPIClient
    from nwbinspector import inspect_nwb

    dandiset_id = "..."  # for example, 000004
    dandiset_type = "draft"  # or "published", if it has an official doi associated

    messages = []
    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id, dandiset_type)
        for asset in dandiset.get_assets():
            s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)
            messages.extend(list(inspect_nwb(nwbfile_path=s3_url, driver="ros3")))




Format Reports
--------------

Reports aggregate messages into a readable form.

.. code-block:: python

    from nwbinspector.inspector_tools import format_messages

    print("\n".join(format_messages(messages, levels=["importance", "file_path"])))

The `levels` argument can be altered to change the nesting structure of the report. Any combination and order
of :py:class:`~nwbinspector.register_checks.InspectorMessage` attributes can be utilized to produce a more easily
readable structure.
