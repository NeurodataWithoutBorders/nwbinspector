.. image:: logo/logo.png

Welcome to the documentation for the NWBInspector!
==================================================

..
  :scale: 100 %
  :align: right

NWBInspector is a Python-based package designed to asses the quality of Neurodata Without Borders
files (NWBFiles) and to suggest improvements for any Best Practice violations that are found.


.. note::

    This package is in alpha development; as such, we make every effort towards
    a stable environment but bugs are known to occur. If you use this software
    for your own quality assurance purposes and discover any issues throughout
    the process, please let us know by filing a ticket on our :nwbinspector-issues: page.

.. toctree::
   :maxdepth: 2

   best_practices/best_practices_index
   user_guide/user_guide
   developer_guide


.. toctree::
    :maxdepth: 2
    :caption: API Documentation

    Check Functions <api/checks>
    Core Functions <api/nwbinspector>
    Data Classes and Check Registration <api/register_check>
    Organization and Display Tools <api/tools>
    Generic Utils <api/utils>


For more information regarding the NWB Standard, please view the `NWB Format Specification <https://nwb-schema.readthedocs.io/en/latest/>`_.

.. Indices and tables
.. ==================
..
.. * :ref:`genindex`
.. * :ref:`modindex`
.. * :ref:`search`
