# -*- coding: utf-8 -*-

# standard library
import logging
from struct import Struct, error as StructError

# project
import protocol

# pack formats (all little endian)
size_fmt = Struct('<H')  # 2 bytes
type_fmt = Struct('<B')  # 1 byte
size_len = size_fmt.size
type_len = type_fmt.size
delimiter_size = 1

# Packet type constants are found in src/network/core/tcp_admin.h
PKG_UNKNOWN = -1
PKT_ADMIN_JOIN = 0
PKT_SERVER_PROTOCOL = 104
PKT_SERVER_WELCOME = 105


# class PacketMeta(type):
#     """
#     Metaclass for Packets
#     allows for server packet_test__ to be defined
#     in a declarative manner
#     """
#     def __new__(cls, name, bases, namespace, **kwargs):
#         if '_fields' in namespace:
#             for field in namespace['_fields']:
#                 namespace[field] = None
#         return super().__new__(cls, name, bases, namespace, **kwargs)

class PacketError(Exception):
    """Base Packet related errors"""
    pass


class PacketConstructionError(PacketError):
    """Error while constructing packet"""
    pass


class PacketEncodeError(PacketError):
    """Error while encoding packet"""
    def __init__(self, msg):
        super().__init__('Error while encoding packet: %s' % msg)


class PacketDecodeError(PacketError):
    """Error while decoding packet"""
    def __init__(self, msg):
        super().__init__('Error while decoding packet: %s' % msg)


class Packet:
    """
    A packet to be sent or received trough the admin TCP connection

    The _field attribute allows for a declarative description
    of the packet format

    ** TODO explain _field format **
    """
    _fields = []
    log = logging.getLogger('Packet')
    strict_magic_encode = False  # set this to True to have strict magic_encode
    strict_magic_decode = False  # set this to True to have strict magic_decode

    pkt_size_type = protocol.UInt16             # the type of the package-size field
    pkt_size_size = pkt_size_type.struct.size   # the size of the package-size field
    pkt_type_type = protocol.UInt8              # the type of the package-type field
    pkt_type_size = pkt_type_type.struct.size   # the size of the package-type field

    def __init__(self, size=None):
        self.size = size
        self.log = logging.getLogger(self.__class__.__name__)
        for f in self._fields:
            setattr(self, f[0], None)


class AdminPacket(Packet):
    """Packets sent by admin"""
    log = logging.getLogger('AdminPacket')

    def __init__(self, **kwargs):
        super().__init__(None)
        # will be set once we encode the packet
        self._raw_data = None
        # kwargs
        if len(kwargs) > 0:
            for f in self._fields:
                field_name = f[0]
                if field_name in kwargs:
                    setattr(self, field_name, kwargs[field_name])

    def _magic_encode(self):
        """Encodes package according to _fields attribute"""
        try:
            for name, encoder in self._fields:
                field = getattr(self, name)
                if type(encoder) is type and issubclass(encoder, protocol.Type):
                    # It's a subclass of protocol.Type
                    self._raw_data += encoder.encode(field)
                elif isinstance(encoder, str):
                    self._raw_data += getattr(self, encoder)(field)
        except StructError as e:
            if self.strict_magic_encode:
                raise PacketEncodeError(str(e))
            else:
                self.log.exception('Error while encoding packet')

    def encode(self):
        """Encodes packet to bytes ready to be sent through TCP connection"""
        self._raw_data = b''
        # encoding payload
        self._magic_encode()
        # prepending packet size and type
        self._raw_data = self._get_encoded_packet_size() + \
                         self._get_encoded_packet_type() + \
                         self._raw_data

    def encoded(self):
        if self._raw_data is None:
            self.encode()
        return self._raw_data

    def _get_encoded_packet_type(self):
        """Returns encoded packet type field"""
        return self.pkt_type_type.encode(self.type_)

    def _get_encoded_packet_size(self):
        """
        Returns size of encoded package,
        this method must be called after the package payload has been encoded
        """
        # packet size is size + type + payload
        pkt_size = self.pkt_size_size + self.pkt_type_size + len(self._raw_data)
        return self.pkt_size_type.encode(pkt_size)


class ServerPacket(Packet):
    """Packets send by server"""
    log = logging.getLogger('ServerPacket')

    def __init__(self, raw_data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # used when decoding raw data
        self.index = 0
        # raw data as received from network
        self.raw_data = raw_data

    def magic_decode(self):
        try:
            for name, decoder in self._fields:
                if type(decoder) is type and issubclass(decoder, protocol.Type):
                    # if it is a class and an instance of proto.Type we decode it
                    setattr(self, name, self._decode_field(decoder))
                elif isinstance(decoder, str):
                    # if it is a string we assume it is the name of a method
                    setattr(self, name, getattr(self, decoder)())
                else:
                    # otherwise we assume it is a method
                    setattr(self, name, decoder())
        except StructError as e:
            if self.strict_magic_decode:
                raise PacketDecodeError(str(e))
            else:
                self.log.exception('Error while decoding packet')

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
        # getting packet type
        packet_type = cls.pkt_type_type.decode(raw_data, index=2)[0]
        raw_data = raw_data[cls.pkt_size_type.struct.size + cls.pkt_type_type.struct.size:packet_size]
        # looking for class to instantiate
        try:
            class_ = packet_map[packet_type]
        except KeyError as e:
            cls.log.error('Unknown packet type: %s, keeping raw data', packet_type)
            return UnknownServerPacket(packet_size, raw_data)
        # creating package
        p = class_(packet_size, raw_data)
        p.magic_decode()
        return p


# ##### AdminPacket - packet_test__ sent from client to server #####################
class AdminJoinPacket(AdminPacket):
    type_ = 0
    _fields = [
        ('password',    protocol.String),
        ('name',        protocol.String),
        ('version',     protocol.String),
    ]


# ##### ServerPackets - packet_test__ sent from server to client ###################
class UnknownServerPacket(ServerPacket):
    type_ = -1

    def __init__(self, size, raw_data):
        super().__init__(self.type_, size)
        self.raw_data = raw_data


class ServerProtocolPacket(ServerPacket):
    type_ = 103
    _fields = [
        ('version', protocol.UInt8),
        ('supported_update_freqs', '_decode_supported_update_freqs')
    ]

    def __init__(self, size, raw_data):
        super().__init__(type_=self.type_, size=size, raw_data=raw_data)

    def _decode_supported_update_freqs(self):
        res = {}
        param_size = protocol.UInt8.struct.size + (protocol.UInt16.struct.size * 2)
        while self.index + param_size <= len(self.raw_data):
            _ = self._decode_field(protocol.UInt8)  # separator
            key = self._decode_field(protocol.UInt16)
            value = self._decode_field(protocol.UInt16)
            res[key] = value
        _ = self._decode_field(protocol.UInt8)  # final separator
        return res


class ServerWelcomePacket(ServerPacket):
    type_ = 104
    _fields = [
        ('server_name',         protocol.String),
        ('openttd_revision',    protocol.String),
        ('is_dedicated',        protocol.Boolean),
        ('map_name',            protocol.String),
        ('generation_seed',     protocol.UInt32),
        ('landscape',           protocol.UInt8),
        ('game_creation_date',  protocol.Date),
        ('map_size_x',          protocol.UInt16),
        ('map_size_y',          protocol.UInt16),
    ]

    def __init__(self, size, raw_data):
        super().__init__(type_=self.type_, size=size, raw_data=raw_data)


packet_map = {
    PKG_UNKNOWN:            UnknownServerPacket,
    PKT_ADMIN_JOIN:         AdminJoinPacket,
    PKT_SERVER_PROTOCOL:    ServerProtocolPacket,
    PKT_SERVER_WELCOME:     ServerWelcomePacket,
}
