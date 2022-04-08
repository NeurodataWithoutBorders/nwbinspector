from hdmf.testing import TestCase

from nwbinspector.utils import format_byte_size, check_regular_series, is_dict_in_string


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


def test_is_dict_in_string_none():
    string = "not a dict"
    assert is_dict_in_string(string=string) is False


def test_is_dict_in_string_1():
    string = str(dict(a=1))
    assert is_dict_in_string(string=string) is True


def test_is_dict_in_string_2():
    string = str([dict(a=1), dict(b=2)])
    assert is_dict_in_string(string=string) is True


def test_is_dict_in_string_3():
    string = str(dict(a=dict(b=2)))
    assert is_dict_in_string(string=string) is True


def test_is_dict_in_string_4():
    string = "some text: {'then': 'a dict'}"
    assert is_dict_in_string(string=string) is True
