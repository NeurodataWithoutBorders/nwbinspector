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



.. _advanced_streaming_api:

Fetching and inspecting individual DANDI assets (ROS3)
------------------------------------------------------

While the section explaining :ref:`basic steaming of a dandiset <simple_streaming_api>` covered the simplest and most convenient usage of the streaming feature, sometimes a greater degree of control or customization is required. The :py:attr:`driver` argument of the :py:class:`~pynwb.NWBHDF5IO` can be passed directly into our core inspection functions. In this case, the :py:attr:`path` or :py:attr:`nwbfile_path` arguments become the full S3 path on the DANDI archive. Resolution of these paths can be performed via the following code...


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

.. note::

    Since the :py:attr:`driver` argument can be passed directly into PyNWB, it should also be possible to utilize :alternative-streaming-tutorial:`alternative streaming methods <>` with the NWB Insector API.

.. note::

    More generally, you are able to specify any S3 path to any bucket to which you have the proper AWS access credentials for.



Format Reports
--------------

Reports aggregate messages into a readable form.

.. code-block:: python

    from nwbinspector.inspector_tools import format_messages

    print("\n".join(format_messages(messages, levels=["importance", "file_path"])))

The `levels` argument can be altered to change the nesting structure of the report. Any combination and order
of :py:class:`~nwbinspector.register_checks.InspectorMessage` attributes can be utilized to produce a more easily
readable structure.
