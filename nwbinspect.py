import sys
from pathlib import Path
import pynwb
import numpy as np


def main(dir_name):
    data_dir = Path(dir_name)
    if not data_dir.is_dir():
        raise Exception('%s should be a directory' % dir_name)

    dir_files = list(data_dir.glob('*.nwb'))

    for fi, filename in enumerate(dir_files):
        print('%d/%d %s' % (fi + 1, len(dir_files), filename))

        try:
            with pynwb.NWBHDF5IO(str(filename), 'r') as io:
                pynwb.validate(io)
                nwbfile = io.read()
                # inspect NWBFile object

                # check dataset values in timeseries
                for ts in all_timeseries(nwbfile):
                    if ts.data is None:
                        error_code = 'A101'
                        print("%s: %s %s data is None" % (error_code, type(ts), ts.name))
                        continue

                    uniq = np.unique(ts.data)
                    if len(uniq) == 1:
                        error_code = 'A101'
                        print("%s: '%s' %s data has all values = %s" % (error_code, ts.name, type(ts), uniq[0]))
                    elif np.array_equal(uniq, [0., 1.]):
                        error_code = 'A101'
                        print("%s: '%s' %s data should be type boolean instead of %s"
                              % (error_code, ts.name, type(ts), ts.data.dtype))
                    elif len(uniq) == 2:
                        error_code = 'A101'
                        print("%s: '%s' %s data has only unique values %s. Consider storing the data as boolean."
                              % (error_code, ts.name, type(ts), uniq))
                    elif len(uniq) <= 4:
                        print("NOTE: '%s' %s has only unique values: %s" % (ts.name, type(ts), uniq))

                    # check whether rate should be used instead of timestamps
                    time_tol_decimals = 9
                    uniq_diff_ts = np.unique(np.diff(ts.timestamps).round(decimals=time_tol_decimals))
                    if len(uniq_diff_ts) == 1:
                        error_code = 'A101'
                        print("%s: '%s' %s timestamps should use starting_time %f and rate %f"
                              % (error_code, ts.name, type(ts), ts.timestamps[0], uniq_diff_ts[0]))

        except Exception as ex:
            print(ex)
        print()


def all_timeseries(nwbfile):
    for obj in nwbfile.objects.values():
        if isinstance(obj, pynwb.TimeSeries):
            yield obj


if __name__ == '__main__':
    """
    Usage: python nwbinspect.py dir_name
    """
    main(sys.argv[1])
