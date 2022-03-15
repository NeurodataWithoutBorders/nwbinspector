Using the Library: Advanced
===========================

This is a collection of tutorials illustrating some of the more advanced uses of the NWBInspector


Yielding and Iterating
----------------------

Both the `inspect_all` and `inspect_nwb` functions directly return generators. That is, they do not actually run any
checks on any NWBFile until the user performs an iteration command on them. In the basic usage, we recommend the
simplest way of doing this as simply casting the generator as a list, i.e, `list(inspect_nwb(...))` which will
automatically collapse the iteration.

However, if a user chooses, they can harness these generators in more sophisticated ways, such as

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    first_message = next(results_generator)

which will return either the first `InspectorMessage` for the first Best Practice issue detected in the file (if any),
or it will raise a `StopIteration` error. This error can be caught in the following manner

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    try:
        first_message = next(results_generator)
    except StopIteration:
        print("There are no messages!")

Of course, the generator can be treated as any other iterable as well, such as with `for` loops

.. code-block:: python

    results_generator = inspect_nwb(nwbfile_path="path_to_single_nwbfile")

    for message in results_generator:
        print(message)


Running on a DANDISets (ros3)
-----------------------------

It is a common use case to want to inspect and review entire datasets of NWBFiles that have already been
uploaded to the DANDI archive (TODO: add link). While one could technically just download the DANDISet and
use the NWBInspector as normal, there is another, less expensive possibility in terms of bandwith. This is especially
useful when the underlying dataset is quite large and thus impractical to download - some DANDISets can even be on the TB scale!

The general tutorial for using the `ros3` driver can be found here (TODO: add link). This driver can be passed directly
into our core inspection functions, and the `path` or `nwbfile_path` arguments in this case become the S3 path on the
DANDI archive. Resolution of these paths can be performed via the following code

.. code-block:: python

    from dandi.dandiapi import DandiAPIClient
    from nwbinspector import inspect_nwb

    dandiset_id = "..."  # for example, 000004
    dandiset_type = "draft"  # or "published", if it has an official doi associated

    with DandiAPIClient() as client:
        dandiset = client.get_dandiset(dandiset_id, dandiset_type)
        for asset in dandiset.get_assets():
            asset = dandiset.get_asset_by_path(asset.path)
            s3_url = asset.get_content_url(follow_redirects=1, strip_query=True)
            messages = list(inspect_nwb(nwbfile_path=s3_url, driver="ros3"))




Organization of Reports
-----------------------

Our organization functions are capable of arbitrary nesting based on attributes of the InspectorMessage class...

.. code-block:: python

    from nwbinspector.inspector_tools import organize_messages

    organized_messages = organized_messages(messagess=list(inspect_all(...)), levels=["file_path", "importance"])

This will return a nested dictionary of the same depth as as `levels`, with each key being the unique values within
that nested condition. While `levels = ["file_path", "importance"]` is the default behavior, any combination and order
of `InspectorMessage` attributes can be utilized to produce a more easily readable structure.
