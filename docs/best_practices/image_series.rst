ImageSeries
===========

Storage of ImageSeries
----------------------

.. _best_practice_use_external_mode:

Use external mode for videos of animals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When storing videos of natural behavior using the :ref:`nwb-schema:sec-ImageSeries` the file should be stored as
an external file. That is, the file should be packaged together with the nwb file instead of stored inside the format.
This can be accomplished by using  the ``external_file`` file option to store the path instead. This is preferred for
videos because it allows the usage of video compression codecs that are lossy and highly optimized for such videos.

Check function: :py:meth:`~nwbinspector.checks._image_series.check_image_series_data_size`


Use internal dataset for videos of neurophysiological data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When storing a :ref:`nwb-schema:sec-TwoPhotonSeries` or other videos of neural data, lossy compression should not be used,
and it is best to store the this data within a Dataset in the NWB file and use chunking and lossless compression to reduce
the disk space.


.. _best_practice_image_series_external_file_relative:

Use relative path for external mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When using ``external_file`` the paths passed in the ``external_file`` option should be relative to the location of the nwb file.

Check function: :py:meth:`~nwbinspector.checks._image_series.check_image_series_external_file_relative`


.. _best_practice_starting_frame_only_with_external_file:

Starting frame only with external file
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``starting_frame`` attribute of an :ref:`nwb-schema:sec-ImageSeries` is only relevant when using external files.
If there is no external file, there should be no starting frame set. This is a legacy issue that was possible in
older versions of PyNWB (< 2.2.0).

Check function: :py:meth:`~nwbinspector.checks._image_series.check_image_series_starting_frame_without_external_file`


Video Files
-----------


.. _best_practice_external_file_format:

Use a standard video container and codec
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The format of a video has two parts, the codec that the frames are encoded with and the container that holds them,
and the right choice for each depends on whether the video is lossy or lossless.

For lossy video, use H.264, VP8, VP9 or AV1 in an MP4 or WebM container. All four codecs are efficient and play
everywhere, and which of them to pick depends on the tooling and hardware available. H.264 is covered by patents
managed through a patent pool, while VP8, VP9 and AV1 are royalty-free. MP4 and WebM are the two containers that every
platform supports and the only two a browser can play: Safari supports neither Matroska (``.mkv``) nor the other
legacy containers, and the
`MDN container guide <https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Containers>`_ lists MP4 and
WebM as the only two with universal support. Most scientific video is in ``.avi`` or ``.mov`` with a legacy codec such
as MJPEG, MPEG-4 Part 2 (``mp4v``, DIVX, XVID), WMV or DV, because that is what the camera SDK or the operating system
produced by default, not because either was chosen.

When only the container is wrong, no re-encoding is needed. The stream is copied byte for byte and only the container
headers are rewritten, which takes seconds even for a large file: ``ffmpeg -i input.mkv -c copy output.mp4``. When the
codec is wrong the re-encoding settles both at once:
``ffmpeg -i input.avi -c:v libx264 -crf 18 -pix_fmt yuv420p output.mp4``.

For lossless video, use FFV1. It compresses two to three times smaller than uncompressed video with identical pixel
values, adds per-frame checksums, and handles grayscale and high bit depth without the chroma subsampling that
consumer codecs impose, which is why the preservation community standardised on it. FFV1 is normally paired with MKV,
but the container makes no practical difference here: every tool that reads FFV1 handles MKV and AVI alike, and no
browser decodes lossless video whatever it is held in. Lossless data should never be re-encoded to a lossy codec.

Check function: :py:meth:`~nwbinspector.checks._image_series.check_image_series_external_file_format`
