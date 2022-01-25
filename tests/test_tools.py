"""Authors: Cody Baker and Ben Dichter."""
import numpy as np
from uuid import uuid4
from datetime import datetime

import pynwb

from nwbinspector.tools import all_of_type


def test_all_of_type():
    nwbfile = pynwb.NWBFile(
        session_description="Testing inspector.",
        identifier=str(uuid4()),
        session_start_time=datetime.now().astimezone(),
    )
    true_time_series = [
        pynwb.TimeSeries(name=f"time_series_{x}", data=np.zeros(shape=(100, 10)), rate=1.0) for x in range(4)
    ]
    for x in range(2):
        nwbfile.add_acquisition(true_time_series[x])
    ecephys_module = nwbfile.create_processing_module(name="ecephys", description="")
    ecephys_module.add(true_time_series[2])
    ophys_module = nwbfile.create_processing_module(name="ophys", description="")
    ophys_module.add(true_time_series[3])

    nwbfile_time_series = [obj for obj in all_of_type(nwbfile=nwbfile, neurodata_type=pynwb.TimeSeries)]
    for time_series in true_time_series:
        assert time_series in nwbfile_time_series
