# -*- coding: utf-8 -*-

# standard library
from datetime import date

# related
import pytest

# project
import packet
from protocol import *


@pytest.mark.parametrize('params', [
    # kwargs             expected-values
    ({},                 [None, None, None, None]),
    ({'f3': 3},          [None, None, 3, None]),
    ({'f1': 1, 'f2': 2}, [1, 2, None, None]),
    ({'f4': 4, 'xx': 2}, [None, None, None, 4]),
    ({'xx': 3},          [None, None, None, None])

])
def test_admin_packet_construction(params):
    class TestAdminPacket(packet.AdminPacket):
        type_ = 99
        _fields = [
            ('f1', None),
            ('f2', None),
            ('f3', None),
            ('f4', None),
        ]
    kwargs, expected = params
    tap = TestAdminPacket(**kwargs)
    assert [tap.f1, tap.f2, tap.f3, tap.f4] == expected, 'Field values do not match'


def test_admin_packet_magic_encode():

    class TestAdminPacket(packet.AdminPacket):
        type_ = 99

        def __init__(self, xx=None, **kwargs):
            super().__init__(**kwargs)
            self._raw_data = b''

        def my_custom_encode(self, data):
            res = b''
            for k, v in data.items():
                res += String.encode(k)
                res += UInt8.encode(v)
            return res

        _fields = [
            ('boolean_field',       Boolean),
            ('date_field',          Date),
            ('string_field',        String),
            ('uint8_field',         UInt8),
            ('uint16_field',        UInt16),
            ('uint32_field',        UInt32),
            ('method_name_field',   'my_custom_encode'),
        ]

    values = {
        'boolean_field':        True,
        'date_field':           date(1985, 5, 7),
        'string_field':         'öä£đßŋ{}đðł{',
        'uint8_field':          32,
        'uint16_field':         12354,
        'uint32_field':         4354132,
        'method_name_field':    {'c': 3, 'd': 4},
    }

    tap = TestAdminPacket(**values)
    tap._magic_encode()

    expected_stream = Boolean.encode(values['boolean_field']) + \
                      Date.encode(values['date_field']) + \
                      String.encode(values['string_field']) + \
                      UInt8.encode(values['uint8_field']) + \
                      UInt16.encode(values['uint16_field']) + \
                      UInt32.encode(values['uint32_field']) + \
                      tap.my_custom_encode(values['method_name_field'])

    assert tap._raw_data == expected_stream, 'Encoded stream does not match'


# TODO test_admin_packet_encode

# TODO test_server_packet_decode

# TODO test_server_packet_magic_decode
