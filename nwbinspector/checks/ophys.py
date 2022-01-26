"""Authors: Cody Baker, Ben Dichter, and Ryan Ly."""
import pynwb

from ..tools import all_of_type
from ..utils import nwbinspector_check


# @nwbinspector_check(severity=2, neurodata_type=pynwb.TimeSeries)
# def check_ophys(nwbfile):
#     opto_sites = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticStimulusSite))
#     opto_series = list(all_of_type(nwbfile, pynwb.ogen.OptogeneticSeries))
#     for site in opto_sites:
#         if not site.description:
#             error_code = "A101"
#             print(
#                 "%s: '%s' %s is missing text for attribute 'description'" % (error_code, site.name, type(site).__name__)
#             )
#         if not site.location:
#             error_code = "A101"
#             print("%s: '%s' %s is missing text for attribute 'location'" % (error_code, site.name, type(site).__name__))
#     if opto_sites and not opto_series:
#         error_code = "A101"
#         print("%s: OptogeneticStimulusSite object(s) exists without an OptogeneticSeries" % error_code)
