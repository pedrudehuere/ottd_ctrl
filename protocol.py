# -*- coding: utf-8 -*-

# standard library
from datetime import date, timedelta
from enum import Enum
from pprint import pformat
from struct import Struct, error as StructError

# project
from const import NetworkVehicleType, NetworkVehicleTypeStr

ZERO_BYTE = b'\x00'
ENCODING = 'utf8'  # TODO verify
STRING_DELIMITER = ZERO_BYTE
MAX_PACKET_SIZE = 1460
EPOCH_DATE = date(year=1, month=1, day=1)


bool_fmt = Struct('<?')
bool_size = 1


class TypeError(Exception):
    pass


class FieldEncodeError(TypeError):
    pass


class FieldDecodeError(TypeError):
    pass


class StringDecodeError(FieldDecodeError):
    pass


class Type:
    def __init__(self, value=None, raw_data=None):
        """

        :param value:
        :param raw_data: Bytes, must start with the field, but can be longer,
                         the bytes after the decoded field are ignored
        """
        assert value is not None or raw_data is not None, \
            "Need wither 'value' or 'raw_data'"
        self._value = value
        self._raw_data = raw_data
        self._raw_size = None

    @property
    def value(self):
        if self._value is None:
            self.decode()
        return self._value

    @property
    def raw_data(self):
        if self._raw_data is None:
            self.encode()
        return self._raw_data

    @property
    def raw_size(self):
        """Size in bytes of the encoded value"""
        if self._raw_size is None:
            self.encode()
        return self._raw_size

    def encode(self):
        """Sets value and size from decoded raw data"""
        raise NotImplementedError('Must be implemented')

    def decode(self):
        """Sets raw data from encoded value"""
        raise NotImplementedError('Must be implemented')


class CompositeType(Type):
    """A higher level type made of other types"""
    _fields = []

    def pretty(self):
        # TODO test
        return pformat({f[0]: getattr(self, f[0]) for f in self._fields})


class NumberType(Type):
    """
    Must have a struct attribute, the size of these types is known in advance
    """
    struct = None

    def encode(self):
        try:
            self._raw_data = self.struct.pack(self._value)
        except StructError as e:
            raise FieldEncodeError(str(e))

    def decode(self):
        try:
            self._value = self.struct.unpack_from(self._raw_data)[0]
        except StructError as e:
            raise FieldDecodeError(str(e))

    @property
    def raw_size(self):
        return self.struct.size


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


class Boolean(NumberType):
    struct = UInt8.struct

    def encode(self):
        self._raw_data = UInt8(value=1 if bool(self._value) else 0).raw_data

    def decode(self):
        self._value = bool(UInt8(raw_data=self._raw_data).value)


class Date(NumberType):
    struct = UInt32.struct

    def encode(self):
        self._raw_data = UInt32(value=(self._value - EPOCH_DATE).days + 366).raw_data

    def decode(self):
        self._value = EPOCH_DATE + timedelta(days=UInt32(raw_data=self._raw_data).value - 366)


class String(Type):
    def encode(self):
        self._raw_data = self._value.encode(ENCODING) + STRING_DELIMITER
        self._raw_size = len(self._raw_data)

    def decode(self):
        separator_index = self.raw_data.find(STRING_DELIMITER)
        if separator_index == -1:
            raise StringDecodeError('No separator found')
        raw_string = self._raw_data[:separator_index]
        try:
            self._value = raw_string.decode(ENCODING)
        except UnicodeDecodeError as e:
                raise StringDecodeError(str(e))
        self._raw_size = len(raw_string) + len(STRING_DELIMITER)


# TODO fix these composite things
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
