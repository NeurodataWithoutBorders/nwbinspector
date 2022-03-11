Using the Library: Advanced
===========================

This is a collection of tutorials illustrating some of the more advanced uses of the NWBInspector


Running on a DANDISets (ros3)
-----------------------------

It is a common use case to want to inspect and review entire datasets of NWBFiles that have already been
uploaded to the DANDI archive (TODO: add link). While one could technically just download the DANDISet and
use the NWBInspector as normal, there is another, less expensive possibility in terms of bandwith. This is especially 
useful when the underlying dataset is quite large - some DANDISets can even be on the TB scale!

Resolving an S3 Path and Passing to Inspector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The general tutorial for using the `ros3` driver can be found here (TODO: add link).

Paralleizing the Resolver
~~~~~~~~~~~~~~~~~~~~~~~~~

For enchanced speed, you can easily parallelize the collection of these paths by the following method.


Organization of Reports
-----------------------

Our organization functions are capable of arbitrary nesting based on attributes of the InspectorMessage class...
