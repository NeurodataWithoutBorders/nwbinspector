"""Helper functions related to NWB for internal use that rely on external dependencies (i.e., pynwb)."""

from pynwb import NWBFile


def all_of_type(nwbfile: NWBFile, neurodata_type):
    """Iterate over all objects inside an NWBFile object and return those that match the given neurodata_type."""
    for obj in nwbfile.objects.values():
        if isinstance(obj, neurodata_type):
            yield obj


def get_nwbfile_path_from_internal_object(obj):
    """Determine the file path on disk for a NWBFile given only an internal object of that file."""
    if isinstance(obj, NWBFile):
        return obj.container_source
    return obj.get_ancestor("NWBFile").container_source
