# -*- coding: utf-8 -*-

# standard library
from datetime import date, timedelta
import logging
from struct import pack, Struct, error as StructError

# project
import protocol as proto

# pack formats (all little endian)
size_fmt = Struct('<H')  # 2 bytes
type_fmt = Struct('<B')  # 1 byte
size_len = size_fmt.size
type_len = type_fmt.size
delimiter_size = 1

# used to convert dates received from OpenTTD server
# EPOCH_DATE = date(year=1, month=1, day=1)


# class PacketMeta(type):
#     """
#     Metaclass for Packets
#     allows for server packets to be defined
#     in a declarative manner
#     """
#     def __new__(cls, name, bases, namespace, **kwargs):
#         if '_fields' in namespace:
#             for field in namespace['_fields']:
#                 namespace[field] = None
#         return super().__new__(cls, name, bases, namespace, **kwargs)


class Packet():
    _fields = []
    log = logging.getLogger('Packet')
    pkg_size_type = proto.UInt16  # the type of the package-size field
    pkg_type_type = proto.UInt8  # the type of the package-type field

    def __init__(self, type_, size=None):
        self.type_ = type_
        self.size = size
        self.log = logging.getLogger(self.__class__.__name__)
        for f in self._fields:
            setattr(self, f[0], None)


class AdminPacket(Packet):
    """Packets sent by admin"""
    log = logging.getLogger('AdminPacket')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = 0
        self._raw_data = b''

    def magic_encode(self):
        raise NotImplementedError('Must be implemented')

    def encode(self):
        """Encodes packet to bytes ready to be sent through TCP connection"""
        raise NotImplementedError('Must be implemented')


class ServerPacket(Packet):
    """Packets send by server"""
    log = logging.getLogger('ServerPacket')

    def __init__(self, raw_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = 0
        self.raw_data = raw_data

    def magic_decode(self):
        for field in self._fields:
            if type(field[1]) is type and issubclass(field[1], proto.Type):
                # if it is a class and an instance of proto.Type we decode it
                setattr(self, field[0], self._decode_field(field[1]))
            elif isinstance(field[1], str):
                # if it is a string we assume it is the name of a method
                setattr(self, field[0], getattr(self, field[1])())
            else:
                # otherwise we assume it is a method
                setattr(self, field[0], field[1])

    def _decode_field(self, field_type):
        """
        Decodes a given field type from raw_data and updates index
        :param field_type: A protocol.Type subclass
        :returns: The decoded field
        """
        decoded_field, size = field_type.decode(self.raw_data, self.index)
        self.index += size
        return decoded_field

    @classmethod
    def decode(cls, packet_size, raw_data):
        """
        Returns a packet from given bytes
        :param packet_size: The size of the packet in bytes (including the size bytes)
        :param raw_data: bytes (including size bytes)
        """
        packet_type = cls.pkg_type_type.decode(raw_data, index=2)[0]
        raw_data = raw_data[cls.pkg_size_type.struct.size + cls.pkg_type_type.struct.size:packet_size]
        try:
            class_ = packet_map[packet_type]
        except KeyError as e:
            cls.log.error('Unknown packet type: %s, keeping raw data', packet_type)
            return UnknownServerPacket(packet_size, raw_data)
        p = class_(packet_size, raw_data)
        p.magic_decode()
        return p


# ##### AdminPacket - packets sent from client to server #####################
class AdminJoin(AdminPacket):
    type_ = 0

    def __init__(self, name, password, version):
        super().__init__(self.type_)
        self.name = name
        self.password = password
        self.version = version

    def encode(self):
        name = self.name.encode('utf8') + proto.STRING_DELIMITER
        password = self.password.encode('utf8') + proto.STRING_DELIMITER
        version = self.version.encode('utf8') + proto.STRING_DELIMITER
        packet_size = size_len + type_len + len(password) + len(name) + len(version)
        size = size_fmt.pack(packet_size)
        type = type_fmt.pack(self.type_)
        return size + type + password + name + version


# ##### ServerPackets - packets sent from server to client ###################
class UnknownServerPacket(ServerPacket):
    type_ = -1

    def __init__(self, size, raw_data):
        super().__init__(self.type_, size)
        self.raw_data = raw_data


class ServerProtocolPacket(ServerPacket):
    type_ = 103
    _fields = [
        ('version', proto.UInt8),
        ('supported_update_freqs', '_decode_supported_update_freqs')
    ]

    def __init__(self, size, raw_data):
        super().__init__(type_=self.type_, size=size, raw_data=raw_data)

    def _decode_supported_update_freqs(self):
        res = {}
        param_size = proto.UInt8.struct.size + (proto.UInt16.struct.size * 2)
        try:
            while self.index + param_size <= len(self.raw_data):
                _ = self._decode_field(proto.UInt8)  # separator
                key = self._decode_field(proto.UInt16)
                value = self._decode_field(proto.UInt16)
                res[key] = value
            _ = self._decode_field(proto.UInt8)  # final separator
        except StructError as e:
            self.log.exception("Error while decoding")
        return res


class ServerWelcomePacket(ServerPacket):
    type_ = 104
    _fields = [
        ('server_name',         proto.String),
        ('openttd_revision',    proto.String),
        ('is_dedicated',        proto.Boolean),
        ('map_name',            proto.String),
        ('generation_seed',     proto.UInt32),
        ('landscape',           proto.UInt8),
        ('game_creation_date',  proto.Date),
        ('map_size_x',          proto.UInt16),
        ('map_size_y',          proto.UInt16),
    ]

    def __init__(self, size, raw_data):
        super().__init__(type_=self.type_, size=size, raw_data=raw_data)


packet_map = {
    -1:     UnknownServerPacket,
    103:    ServerProtocolPacket,
    104:    ServerWelcomePacket,
}
