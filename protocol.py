# -*- coding: utf-8 -*-

# standard library
from datetime import date, timedelta
from enum import Enum
from pprint import pformat
from struct import Struct

# project
from const import NetworkVehicleType, NetworkVehicleTypeStr

ZERO_BYTE = b'\x00'
ENCODING = 'utf8'  # TODO verify
STRING_DELIMITER = b'\x00'
MAX_PACKET_SIZE = 1460
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

    @classmethod
    def encode(cls, value):
        """
        Decodes given value as bytes
        :param value: Value do be encoded
        :return: bytes
        """
        raise NotImplementedError('Must be implemented')


class CompositeType(Type):
    """A higher level type made of other types"""
    _fields = []

    def pretty(self):
        # TODO test
        return pformat({f[0]: getattr(self, f[0]) for f in self._fields})


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


class UInt64(NumberType):
    struct = Struct('<Q')


class SInt64(NumberType):
    struct = Struct('<q')


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
        return raw_string.decode(ENCODING), len(raw_string) + len(STRING_DELIMITER)

    @classmethod
    def encode(cls, the_string):
        return the_string.encode(ENCODING) + STRING_DELIMITER


class Date(UInt32):
    @classmethod
    def decode(cls, raw_data, index=None):
        # OpenTTD server sends dates as number of days since day 0,
        # but since datetime does not support dates before 1.1.1
        # we have to subtract 366 days (because year 0 is a leap year)
        number, size = super().decode(raw_data, index)
        return EPOCH_DATE + timedelta(number - 366), size

    @classmethod
    def encode(cls, the_date):
        return super().encode((the_date - EPOCH_DATE).days + 366)


class CompanyEconomy(CompositeType):
    """Contains economy information for a company"""
    _fields = [
        ('company_id',              UInt8),
        ('money',                   SInt64),  # British Pound
        ('current_loan',            UInt64),
        ('income',                  SInt64),  # current year
        ('delivered_cargo',         UInt16),  # current quarter
        ('company_value_0',         UInt64),
        ('performance_history_0',   UInt16),
        ('delivered_cargo_0',       UInt16),
        ('company_value_1',         UInt64),
        ('performance_history_1',   UInt16),
        ('delivered_cargo_1',       UInt16),
    ]
    size = sum(f[1].struct.size for f in _fields)

    def __init__(self,
                 company_id,
                 money,
                 current_loan,
                 income,
                 delivered_cargo,  # TODO total or the last quarter?
                 stats_2_quarters):
        """
        :param company_id:
        :param money:
        :param current_loan:
        :param income:
        :param total_delivered_cargo:
        :param stats: value, performance and delivered_cargo in the last 2 quarters
        """
        self.company_id = company_id
        self.money = money
        self.current_loan = current_loan
        self.income = income
        self.delivered_cargo = delivered_cargo
        self.stats_2_quarters = stats_2_quarters

    @classmethod
    def decode(cls, raw_data, index=None):
        params = {}
        for name, type_ in cls._fields:
            params[name], size = type_.decode(raw_data, index)
            index += size

        params['stats_2_quarters'] = [
            {
                'company_value':       params['company_value_0'],
                'parformance_history': params['performance_history_0'],
                'delivery_cargo':      params['delivered_cargo_0']
            },
            {
                'company_value':        params['company_value_1'],
                'parformance_history':  params['performance_history_1'],
                'delivery_cargo':       params['delivered_cargo_1']
            },
        ]
        del params['company_value_0']
        del params['performance_history_0']
        del params['delivered_cargo_0']
        del params['company_value_1']
        del params['performance_history_1']
        del params['delivered_cargo_1']

        return cls(**params), cls.size

    def pretty(self):
        # TODO complete with stats
        return pformat({
            'company ID':       self.company_id,
            'money':            self.money,
            'current_loan':     self.current_loan,
            'income':           self.income,
            'delivered_cargo':  self.delivered_cargo
        }, indent=4)


class CompanyStats(CompositeType):
    """Contains stats for a company"""
    _fields = [
        ('company_id',   UInt8),
        ('vehicles_count', '_decode_vehicle_count'),
        ('stations_count', '_decode_station_count'),
    ]
    size = UInt8.struct.size + \
           NetworkVehicleType.NETWORK_VEH_END * UInt16.struct.size + \
           NetworkVehicleType.NETWORK_VEH_END * UInt16.struct.size

    def __init__(self, company_id, vehicles_count, stations_count):
        self.company_id = company_id
        self.vehicles_count = vehicles_count
        self.stations_count = stations_count

    @classmethod
    def decode(cls, raw_data, index=None):
        params = {}
        params['company_id'], size = UInt8.decode(raw_data, index)
        index += size
        params['vehicles_count'], index = cls._decode_vehicle_count(raw_data, index)
        params['stations_count'], index = cls._decode_station_count(raw_data, index)
        return cls(**params), cls.size

    @classmethod
    def _decode_vehicle_count(cls, raw_data, index):
        res = {}
        for n in range(NetworkVehicleType.NETWORK_VEH_END):
            res[n], size = UInt16.decode(raw_data, index)
            index += size
        return res, index

    @classmethod
    def _decode_station_count(cls, raw_data, index):
        res = {}
        for n in range(NetworkVehicleType.NETWORK_VEH_END):
            res[n], size = UInt16.decode(raw_data, index)
            index += size
        return res, index

    def pretty(self):
        # TODO complete with stats
        return pformat({
            'company ID':       self.company_id,
            'vehicles count':   {NetworkVehicleTypeStr[k]: v
                                 for k, v in self.vehicles_count.items()},
            'stations count':   {NetworkVehicleTypeStr[k]: v
                                 for k, v in self.stations_count.items()},
        }, indent=4)
