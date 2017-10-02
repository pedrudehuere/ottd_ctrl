# -*- coding: utf-8 -*-

# standard library
from datetime import date, timedelta
from enum import Enum
from struct import Struct

CHARSET = 'utf8'  # TODO verify
STRING_DELIMITER = b'\x00'
MAX_PACKET_SIZE = 1460  # the packet size is two bytes
EPOCH_DATE = date(year=1, month=1, day=1)


bool_fmt = Struct('<?')
bool_size = 1

# Type of data found on the wire
Types = Enum(
    'Types',
    'uint8 uint16 uint32 boolean string date',
)


class Type:
    struct = None

    @classmethod
    def decode(cls, raw_data, index=None):
        """
        Decodes given raw_data, optionally starting at index
        :param raw_data: Data to decode
        :param index: Where to start to decode
        :returns: the decoded data and its size in bytes
                  (which sometimes is known only after decoding)
        """
        raise NotImplementedError('Must be implemented')


class NumberType(Type):
    @classmethod
    def decode(cls, raw_data, index=None):
        if index is not None:
            return cls.struct.unpack_from(raw_data, index)[0], cls.struct.size
        else:
            return cls.struct.unpack(raw_data)[0], cls.struct.size

    @classmethod
    def encode(cls, the_number):
        return cls.struct.pack(the_number)


class UInt8(NumberType):
    struct = Struct('<B')


class UInt16(NumberType):
    struct = Struct('<H')


class UInt32(NumberType):
    struct = Struct('<I')


class Boolean(UInt8):
    @classmethod
    def decode(cls, raw_data, index=None):
        number, size = super().decode(raw_data, index)
        return bool(number), size

    @classmethod
    def encode(cls, the_boolean):
        return super().encode(1 if the_boolean else 0)


class String(Type):
    @classmethod
    def decode(cls, raw_data, index=None):
        if index is None:
            index = 0
        raw_string = raw_data[index:index + raw_data[index:].find(STRING_DELIMITER)]
        return raw_string.decode(CHARSET), len(raw_string) + len(STRING_DELIMITER)

    @classmethod
    def encode(cls, the_string):
        return the_string.encode(CHARSET) + STRING_DELIMITER


class Date(UInt32):
    # TODO size
    @classmethod
    def decode(cls, raw_data, index=None):
        # OpenTTD server sends dates as number of days since day 0,
        # but since datetime does not support dates before 1.1.1
        # we have to subtract 366 days (because year 1 is a leap year)
        number, size = super().decode(raw_data, index)
        return EPOCH_DATE + timedelta(number - 366), size

    @classmethod
    def encode(cls, the_date):
        raise NotImplementedError()
