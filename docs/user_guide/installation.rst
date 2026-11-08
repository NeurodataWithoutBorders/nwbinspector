Installation
============

This guide assumes the user is familiar with the goals and structure of the NWB standard.
If you haven't checked it out already, please read the :nwb-overview:`NWB Overview <>`

The NWBInspector tool offers convenient command-line usage via any standard Conda or Python terminal.

To install the package in a Python v3.10+ environment, run:

::

    pip install nwbinspector

To validate HED annotations written with the `ndx-hed <https://github.com/hed-standard/ndx-hed>`_ extension,
install the optional HED dependencies:

::

    pip install "nwbinspector[hed]"

Without them, the NWB Inspector reports each table with HED annotations as not validated.

.. note::

    If you are a :matnwb-src:`MatNWB <>` user, please follow the :conda-install:`Conda installation instructions<>` to
    gain access to a Conda/Python terminal and base environment.


.. note::

    You can also install nwbinspector from the conda-forge release.

    ::

        conda install -c conda-forge nwbinspector
