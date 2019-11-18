import sys
from pathlib import Path
import pynwb


def main(dir_name):
    data_dir = Path(dir_name)
    if not data_dir.is_dir():
        raise Exception('%s should be a directory' % dir_name)

    for filename in data_dir.glob('*.nwb'):
        print(filename)

        try:
            with pynwb.NWBHDF5IO(str(filename), 'r') as io:
                pynwb.validate(io)
                nwbfile = io.read()
                # inspect NWBFile object

        except Exception as ex:
            print(ex)


if __name__ == '__main__':
    """
    Usage: python nwbinspect.py dir_name
    """
    main(sys.argv[1])
