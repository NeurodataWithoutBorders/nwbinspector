"""Authors: Cody Baker and Ben Dichter."""
from collections import defaultdict
import numpy as np

import pynwb
import h5py


def check_dset_size(obj, bytes_threshold=2e6):
    for attr in obj:
        if isinstance(attr, h5py.Dataset):
            if attr.nbytes > bytes_threshold and attr.compression is None:
                return f"Consider enabling compression when writing a large dataset."


def check_regular_timestamps(ts: pynwb.TimeSeries, time_tol_decimals=9):
    if ts.timestamps:
        uniq_diff_ts = np.unique(
            np.diff(ts.timestamps).round(decimals=time_tol_decimals)
        )
        if len(uniq_diff_ts) == 1:
            return (
                "constant sampling rate. Consider using starting_time "
                f"{ts.timestamps[0]} and rate {uniq_diff_ts[0]} instead of using the timestamps array."
            )


def check_data_orientation(ts: pynwb.TimeSeries):

    if ts.data is not None and len(ts.data.shape) > 1:
        if ts.timestamps is not None:
            if not (len(ts.data) == len(ts.timestamps)):
                return (
                    f"{type(ts).__name__} {'ts.name'} data orientation appears to be incorrect. The length of the "
                    "first dimension of data does not match the length of timestamps."
                )
        else:
            if any(ts.data.shape[1:] > ts.data.shape[0]):
                return (
                    f"{type(ts).__name__} '{ts.name}' data orientation appears to be incorrect. Time should be in "
                    "the first dimension, and is usually the longest dimension. Here, another dimension is longer. "
                    "This is possibly correct, but usually indicates that the data is in the wrong orientation."
                )


default_checks = {
    1: {
        pynwb.TimeSeries: [check_regular_timestamps],
        pynwb.NWBContainer: [check_dset_size],
    },
    2: {pynwb.TimeSeries: [check_data_orientation]},
    3: {},
}


def inspect_nwb(
    nwbfile: pynwb.NWBFile, checks=default_checks, severity_threshold: int = 0, skip=None,
):
    """
    Inspect a NWBFile object and return suggestions for improvements according to best practices.

    Parameters
    ----------
    nwbfile : pynwb.NWBFile
        The open NWBFile object to test.
    checks : dictionary, optional
        A nested dictionary specifying which quality checks to run.
        Outer key is severity (between 1 to 3 inclusive, 3 being most severe).
        Each severity is mapped to a dictionary whose keys are NWBFile object types.
        The value of each object type is a list of test functions to run.

        # TODO change the below import
        This can be modified or extended by calling `from nwbinspector.refactor_inspector import default_checks`,
        then updating or appending `default_checks` as desired, then passing into this function call.
    severity_threshold : integer, optional
        Ignores tests with an assigned severity below this threshold.
        Severity has three levels:
            3: most severe
                - probably incorrect data
            2: medium severity
                - possibly incorrect data
                - very suboptimal data representation
            1: low severity
                - improvable data representation
        The default is 0.
    skip: list, optional
        names of checks to skip
    """
    check_results = defaultdict(list)
    for severity, severity_checks in checks.items():
        if severity < severity_threshold:
            continue
        for obj in nwbfile.objects.values():
            for check in severity_checks[type(obj)]:
                if check.__name__ in skip:
                    continue
                output = check(obj)
                if output is None:
                    continue
                check_results[severity] = dict(
                    check=check.__name__,
                    obj_type=type(obj).__name__,
                    obj_name=obj.name,
                    output=output,
                )
    return check_results
