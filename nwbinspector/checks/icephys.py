# """Authors: Cody Baker, Ben Dichter, and Ryan Ly."""
# import pynwb

# from ..tools import all_of_type
# from ..utils import nwbinspector_check

# TODO: break up logic into individual checks
# @nwbinspector_check(severity=2, neurodata_type=pynwb.TimeSeries)
# def check_icephys(nwbfile):
#     for elec in all_of_type(nwbfile, pynwb.icephys.IntracellularElectrode):
#         if not elec.description:
#             error_code = "A101"
#             print(
#                 "- %s: '%s' %s is missing text for attribute 'description'"
#                 % (error_code, elec.name, type(elec).__name__)
#             )
#         if not elec.filtering:
#             error_code = "A101"
#             print(
#                 "- %s: '%s' %s is missing text for attribute 'filtering'"
# % (error_code, elec.name, type(elec).__name__)
#             )
#         if not elec.location:
#             error_code = "A101"
#             print(
#                 "- %s: '%s' %s is missing text for attribute 'location'"
# % (error_code, elec.name, type(elec).__name__)
#             )
