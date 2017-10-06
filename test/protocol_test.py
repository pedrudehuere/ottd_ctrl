# -*- coding: utf-8 -*-

# standard library
from datetime import date
import struct

# related
import pytest

# project
from protocol import *

VALUE_RESULT = 'value_result'


def _test_encode(value_result, type_class):
    """Generic encoding test"""
    value, result = value_result
    if type(result) is type and issubclass(result, Exception):
        try:
            type_class.encode(value)
        except result:
            pass  # ok
        else:
            assert False, "Expected '%s' error did not occur" % str(result)
    else:
        assert type_class.encode(value) == result, 'Encoded value does not match'


def _test_decode(value_result, type_class):
    """Generic decoding test"""
    value, result = value_result
    if type(result) is type and issubclass(result, Exception):
        try:
            type_class.decode(value)
        except result:
            pass  # ok
        else:
            assert False, "Expected '%s' error did not occur" % str(result)
    else:
        assert type_class.decode(value)[0] == result, 'Encoded value does not match'


@pytest.mark.parametrize(VALUE_RESULT, [
    (0,     b'\x00'),
    (1,     b'\x01'),
    (255,   b'\xFF'),
    (256,   struct.error),
    (-1,    struct.error)
])
def test_uint8_encode(value_result):
    _test_encode(value_result, UInt8)


@pytest.mark.parametrize(VALUE_RESULT, [
    (b'\x00',       0),
    (b'\x01',       1),
    (b'\xFF',       255),
    (b'\xFF\x00',   struct.error),
    (b'',           struct.error)

])
def test_uint8_decode(value_result):
    _test_decode(value_result, UInt8)


@pytest.mark.parametrize(VALUE_RESULT, [
    (0,     b'\x00\x00'),
    (1,     b'\x01\x00'),
    (65535, b'\xFF\xFF'),
    (65536, struct.error),
    (-1,    struct.error)
])
def test_uint16_encode(value_result):
    _test_encode(value_result, UInt16)


@pytest.mark.parametrize(VALUE_RESULT, [
    (b'\x00\x00',       0),
    (b'\x01\x00',       1),
    (b'\xFF\xFF',       65535),
    (b'\xFF\x00\x00',   struct.error),
    (b'\x00',           struct.error)

])
def test_uint16_decode(value_result):
    _test_decode(value_result, UInt16)


@pytest.mark.parametrize(VALUE_RESULT, [
    (0,             b'\x00\x00\x00\x00'),
    (1,             b'\x01\x00\x00\x00'),
    ((2 ** 32) - 1, b'\xFF\xFF\xFF\xFF'),
    (2 ** 32,       struct.error),
    (-1,            struct.error)
])
def test_uint32_encode(value_result):
    _test_encode(value_result, UInt32)


@pytest.mark.parametrize(VALUE_RESULT, [
    (b'\x00\x00\x00\x00',       0),
    (b'\x01\x00\x00\x00',       1),
    (b'\xFF\xFF\xFF\xFF',       (2 ** 32) - 1),
    (b'\xFF\x00\x00\x00\x00',   struct.error),
    (b'\x00\x00\x00',           struct.error)

])
def test_uint32_decode(value_result):
    _test_decode(value_result, UInt32)


@pytest.mark.parametrize(VALUE_RESULT, [
    (False, b'\x00'),
    (0,     b'\x00'),
    (True,  b'\x01'),
    (1,     b'\x01'),
    (-1,    b'\x01'),
    (99999, b'\x01')
])
def test_boolean_encode(value_result):
    _test_encode(value_result, Boolean)


@pytest.mark.parametrize(VALUE_RESULT, [
    (date(1, 1, 1), UInt32.encode(366)),
    (date(1950, 1, 1), UInt32.encode(712223))
])
def test_date_encode(value_result):
    _test_encode(value_result, Date)


@pytest.mark.parametrize(VALUE_RESULT, [
    ('Hello world!',    'Hello world!'.encode(ENCODING) + ZERO_BYTE),
    ('éäönđß€łđnðæßĸł', 'éäönđß€łđnðæßĸł'.encode(ENCODING) + ZERO_BYTE)

])
def test_string_encode(value_result):
    _test_encode(value_result, String)
