"""Helper functions for internal use that rely on external dependencies (i.e., pynwb)."""
from pynwb import NWBFile


def all_of_type(nwbfile: NWBFile, neurodata_type):
    """Iterate over all objects inside an NWBFile object and return those that match the given neurodata_type."""
    for obj in nwbfile.objects.values():
        if isinstance(obj, neurodata_type):
            yield obj
