# -*- coding: utf-8 -*-

# standard library
import struct

# related
import pytest

# project
from protocol import *

VALUE_RESULT = 'value_result'
RAW_DATA_RESULT = 'raw_data_result'


def _test_encode(value_result, type_class):
    """Generic encoding test"""
    value, result = value_result
    if type(result) is type and issubclass(result, Exception):
        # we expect an error
        try:
            obj = type_class(value=value)
            obj.encode()
        except result:
            pass  # ok
        else:
            assert False, "Expected '%s' error did not occur" % str(result)
    else:
        # we just compare the values
        obj = type_class(value=value)
        assert obj.raw_data == result, 'Raw data does not match'


def _test_decode(raw_data_result, type_class):
    """Generic decoding test"""
    raw_data, result = raw_data_result
    if type(result) is type and issubclass(result, Exception):
        # we expect an error
        try:
            obj = type_class(raw_data=raw_data)
            obj.decode()
        except result:
            pass  # ok
        else:
            assert False, "Expected '%s' error did not occur" % str(result)
    else:
        # we just compare the values
        obj = type_class(raw_data=raw_data)
        assert obj.value == result, 'Decoded raw_data does not match'


# ##### UInt8 ################################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (0,     b'\x00'),
    (1,     b'\x01'),
    (255,   b'\xFF'),
    (256,   FieldEncodeError),
    (-1,    FieldEncodeError)
])
def test_uint8_encode(value_result):
    _test_encode(value_result, UInt8)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00',       0),
    (b'\x01',       1),
    (b'\xFF',       255),
    (b'\x01\xFF',   1),
    (b'',           FieldDecodeError)

])
def test_uint8_decode(raw_data_result):
    _test_decode(raw_data_result, UInt8)


# ##### UInt16 ###############################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (0,     b'\x00\x00'),
    (1,     b'\x01\x00'),
    (65535, b'\xFF\xFF'),
    (65536, FieldEncodeError),
    (-1,   FieldEncodeError)
])
def test_uint16_encode(value_result):
    _test_encode(value_result, UInt16)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00\x00',       0),
    (b'\x01\x00',       1),
    (b'\xFF\xFF',       65535),
    (b'\x01\x00\xFF',   1),
    (b'\x00',           FieldDecodeError)

])
def test_uint16_decode(raw_data_result):
    _test_decode(raw_data_result, UInt16)


# ##### UInt32 ###############################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (0,             b'\x00\x00\x00\x00'),
    (1,             b'\x01\x00\x00\x00'),
    ((2 ** 32) - 1, b'\xFF\xFF\xFF\xFF'),
    (2 ** 32,       FieldEncodeError),
    (-1,            FieldEncodeError)
])
def test_uint32_encode(value_result):
    _test_encode(value_result, UInt32)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00\x00\x00\x00',       0),
    (b'\x01\x00\x00\x00',       1),
    (b'\xFF\xFF\xFF\xFF',       (2 ** 32) - 1),
    (b'\x01\x00\x00\x00\xFF',   1),
    (b'\x00\x00\x00',           FieldDecodeError)

])
def test_uint32_decode(raw_data_result):
    _test_decode(raw_data_result, UInt32)


# ##### UInt64 ###############################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (0,             b'\x00\x00\x00\x00\x00\x00\x00\x00'),
    (1,             b'\x01\x00\x00\x00\x00\x00\x00\x00'),
    ((2 ** 64) - 1, b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'),
    (2 ** 64,       FieldEncodeError),
    (-1,            FieldEncodeError)
])
def test_uint64_encode(value_result):
    _test_encode(value_result, UInt64)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00\x00\x00\x00\x00\x00\x00\x00',       0),
    (b'\x01\x00\x00\x00\x00\x00\x00\x00',       1),
    (b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF',       (2 ** 64) - 1),
    (b'\x01\x00\x00\x00\x00\x00\x00\x00\xFF',   1),
    (b'\x00\x00\x00\x00\x00\x00\x00',           FieldDecodeError)

])
def test_uint64_decode(raw_data_result):
    _test_decode(raw_data_result, UInt64)


# ##### SInt64 ###############################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (0,                 b'\x00\x00\x00\x00\x00\x00\x00\x00'),
    (1,                 b'\x01\x00\x00\x00\x00\x00\x00\x00'),
    (-1,                b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF'),
    (((2**64)//2) - 1,  b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\x7F'),  # max positive
    (-((2**64)//2),     b'\x00\x00\x00\x00\x00\x00\x00\x80'),  # max negative
    ((2**64)//2,        FieldEncodeError),  # max positive + 1
    (-((2**64)//2) - 1, FieldEncodeError),  # max negative - 1
])
def test_sint64_encode(value_result):
    _test_encode(value_result, SInt64)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00\x00\x00\x00\x00\x00\x00\x00',       0),
    (b'\x01\x00\x00\x00\x00\x00\x00\x00',       1),
    (b'\xFF\xFF\xFF\xFF\xFF\xFF\xFF\xFF',       -1),
    (b'\xff\xff\xff\xff\xff\xff\xff\x7f',       ((2**64)//2)-1),
    (b'\x00\x00\x00\x00\x00\x00\x00\x80',       -((2**64)//2)),
    (b'\x01\x00\x00\x00\x00\x00\x00\x00\xFF',   1),
    (b'\x00\x00\x00\x00\x00\x00\x00',           FieldDecodeError),
])
def test_sint64_decode(raw_data_result):
    _test_decode(raw_data_result, SInt64)


# ##### Boolean ##############################################################
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


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (b'\x00',       False),
    (b'\x01',       True),
    (b'\xFF',       True),
    (b'\x00\x01',   False),
])
def test_boolean_decode(raw_data_result):
    _test_decode(raw_data_result, Boolean)


# ##### Date #################################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    (date(1, 1, 1),     UInt32(366).raw_data),
    (date(1950, 1, 1),  UInt32(712223).raw_data)
])
def test_date_encode(value_result):
    _test_encode(value_result, Date)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    (UInt32(366).raw_data,    date(1, 1, 1)),
    (UInt32(712223).raw_data, date(1950, 1, 1)),
    (UInt32(811902).raw_data, date(2222, 11, 30)),
])
def test_date_decode(raw_data_result):
    _test_decode(raw_data_result, Date)


# ##### String ###############################################################
@pytest.mark.parametrize(VALUE_RESULT, [
    ('Hello world!',    'Hello world!'.encode(ENCODING) + ZERO_BYTE),
    ('éäönđß€łđnðæßĸł', 'éäönđß€łđnðæßĸł'.encode(ENCODING) + ZERO_BYTE),
])
def test_string_encode(value_result):
    _test_encode(value_result, String)


@pytest.mark.parametrize(RAW_DATA_RESULT, [
    ('Hello world!'.encode(ENCODING) + ZERO_BYTE,       'Hello world!'),
    ('éäönđß€łđnðæßĸł'.encode(ENCODING) + ZERO_BYTE,    'éäönđß€łđnðæßĸł'),
    ('No zero byte termination here!'.encode(ENCODING), StringDecodeError),
    ('Hello world!'.encode(ENCODING) + ZERO_BYTE +
     'Rehello world!'.encode(ENCODING) + ZERO_BYTE,     'Hello world!'),
    (b'\xFF' + ZERO_BYTE,                               StringDecodeError)
])
def test_string_decode(raw_data_result):
    _test_decode(raw_data_result, String)
