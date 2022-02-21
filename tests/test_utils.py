from hdmf.testing import TestCase

from nwbinspector.utils import format_byte_size, check_regular_series


def test_format_byte_size():
    assert format_byte_size(byte_size=12345) == "12.35KB"


def test_format_byte_size_in_binary():
    assert format_byte_size(byte_size=12345, units="binary") == "12.06KiB"


class TestFormatByteException(TestCase):
    def test_format_byte_size_units_exception(self):
        with self.assertRaisesWith(
            exc_type=ValueError,
            exc_msg="'units' argument must be either 'SI' (for orders of 1000) or 'binary' (for orders of 1024).",
        ):
            format_byte_size(byte_size=12345, units="test")


def test_check_regular_series():
    assert check_regular_series(series=[1, 2, 3])
    assert not check_regular_series(series=[1, 2, 4])
