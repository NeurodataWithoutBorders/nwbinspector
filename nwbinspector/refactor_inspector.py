"""Authors: Cody Baker and Ben Dichter."""
from collections import defaultdict

import pynwb

from .load_checks import load_checks

default_checks = load_checks()


def inspect_nwb(
    nwbfile: pynwb.NWBFile, checks=default_checks, severity_threshold: int = 0
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
    """
    check_results = defaultdict(list)
    for severity, severity_checks in checks.items():
        if severity > severity_threshold:
            for obj in nwbfile.objects.values():
                for check in severity_checks[type(obj)]:
                    output = check(obj)
                    if output is not None:
                        check_results[severity] = dict(
                            check=check.__name__,
                            obj_type=type(obj).__name__,
                            obj_name=obj.name,
                            output=output,
                        )
    return check_results
