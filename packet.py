# -*- coding: utf-8 -*-

# standard library
import logging
from struct import Struct, error as StructError

# project
from const import AdminUpdateTypeStr, NetworkErrorCodeStr, PacketTypes
import protocol

# pack formats (all little endian)
size_fmt = Struct('<H')  # 2 bytes
type_fmt = Struct('<B')  # 1 byte
size_len = size_fmt.size
type_len = type_fmt.size
delimiter_size = 1


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

    pkt_size_field = protocol.UInt16             # the type of the package-size field
    pkt_size_size = pkt_size_field.struct.size   # the size of the package-size field
    pkt_type_field = protocol.UInt8              # the type of the package-type field
    pkt_type_size = pkt_type_field.struct.size   # the size of the package-type field

    def __init__(self, size=None):
        self.size = size
        self.log = logging.getLogger(self.__class__.__name__)
        for f in self._fields:
            setattr(self, f[0], None)

    def pretty(self):
        """Returns a pretty representation of itself"""
        return ', '.join(['%s: %s' % (field[0], getattr(self, field[0])) for field in self._fields])


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
                value = getattr(self, name)
                if value is None:
                    # we ignore None fields
                    # this works because None (or null)
                    # is not a valid value to send over the network
                    continue
                if type(encoder) is type and issubclass(encoder, protocol.Type):
                    # It's a subclass of protocol.Type
                    self._raw_data += encoder(value).raw_data
                elif isinstance(encoder, str):
                    self._raw_data += getattr(self, encoder)(value)
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
        return self.pkt_type_field(value=self.type_).raw_data

    def _get_encoded_packet_size(self):
        """
        Returns size of encoded packet,
        this method must be called after the package payload has been encoded
        """
        # packet size is size + type + payload
        pkt_size = self.pkt_size_size + self.pkt_type_size + len(self._raw_data)
        return self.pkt_size_field(value=pkt_size).raw_data


class ServerPacket(Packet):
    """Packets send by server"""
    log = logging.getLogger('ServerPacket')

    def __init__(self, size, raw_data, *args, **kwargs):
        super().__init__(size, *args, **kwargs)
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
        field = field_type(raw_data=self.raw_data[self.index:])
        decoded_field = field.value
        self.index += field.raw_size
        return decoded_field

    @classmethod
    def decode(cls, packet_size, raw_data):
        """
        Returns a packet from given bytes
        :param packet_size: The size of the packet in bytes (including the size bytes)
        :param raw_data: bytes (including size bytes)
        """
        # getting packet type
        packet_type = cls.pkt_type_field(raw_data=raw_data[2:]).value
        raw_data = raw_data[cls.pkt_size_field.struct.size + cls.pkt_type_field.struct.size:packet_size]
        # looking for class to instantiate
        class_ = packet_map.get(packet_type, None)
        if class_ is None:
            cls.log.error('Unknown packet type: %s, keeping raw data', packet_type)
            return UnknownServerPacket(packet_size, raw_data)
        # creating package
        p = class_(packet_size, raw_data)
        p.magic_decode()
        return p


# ##### AdminPacket - packet_test__ sent from client to server #####################
class AdminJoinPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_JOIN
    _fields = [
        ('password',    protocol.String),
        ('name',        protocol.String),
        ('version',     protocol.String),
    ]


class AdminQuitPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_QUIT
    _fields = []


class AdminChatPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_CHAT
    _fields = [
        ('network_action',   protocol.UInt8),  # a chat NetworkAction value
        ('destination_type', protocol.UInt8),  # a DestType value
        ('destination',      protocol.UInt32),
        ('message',          protocol.String),
    ]


class AdminPollPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_POLL
    _fields = [
        ('update_type', protocol.UInt8),  # AdminUpdateType value
        ('d1',          protocol.UInt32),
    ]


class AdminRConPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_RCON
    _fields = [
        ('command', protocol.String),
    ]


class AdminUpdateFrequenciesPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_UPDATE_FREQUENCY
    _fields = [
        ('update_type', protocol.UInt16),  # a value of AdminUpdateType
        ('update_frequency', protocol.UInt16),  # a value of AdminUpdateFrequency
    ]


class AdminPingPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_PING
    _fields = [
        ('data', protocol.UInt32),  # Just a number we will receive back from server (PONG)
    ]


class AdminGameScriptPacket(AdminPacket):
    type_ = PacketTypes.ADMIN_PACKET_ADMIN_GAMESCRIPT
    _fields = [
        ('json_string', protocol.String),
    ]


# ##### ServerPackets - packet_test__ sent from server to client ###################
class UnknownServerPacket(ServerPacket):
    type_ = -1

    def __init__(self, size, raw_data):
        super().__init__(self.type_, size)
        self.raw_data = raw_data


class ServerProtocolPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL
    _fields = [
        ('version', protocol.UInt8),
        ('supported_update_freqs', '_decode_supported_update_freqs')
    ]

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

    def pretty(self):
        return ', '.join([str(self.version)] +
                         ['%s: 0x%x' % (AdminUpdateTypeStr[k], v)
                  for k, v in self.supported_update_freqs.items()])


class ServerWelcomePacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_WELCOME
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


class ServerDatePacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_DATE
    _fields = [
        ('date', protocol.Date),
    ]


class ServerRConEndPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_RCON_END
    _fields = [
        ('command', protocol.String),
    ]


class ServerRConPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_RCON
    _fields = [
        ('colour', protocol.UInt16),
        ('result', protocol.String),
    ]


class ServerErrorPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_ERROR
    _fields = [
        ('error', protocol.UInt8),
    ]

    def pretty(self):
        return NetworkErrorCodeStr.get(self.error, 'UNKNOWN')


class ServerPongPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_PONG
    _fields = [
        ('data', protocol.UInt32)
    ]


class ServerGameScriptPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_GAMESCRIPT
    _fields = [
        ('json_string', protocol.String),
    ]


class ServerChatPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CHAT
    _fields = [
        ('network_action',      protocol.UInt8),
        ('destination_type',    protocol.UInt8),
        ('client_id',           protocol.UInt32),
        ('message',             protocol.String),
        ('data',                protocol.UInt64),
    ]


class ServerClientJoinPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CLIENT_JOIN
    _fields = [
        ('client_id', protocol.UInt32),
    ]


class ServerClientInfoPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CLIENT_INFO
    _fields = [
        ('client_id',       protocol.UInt32),
        ('client_address',  protocol.String),
        ('client_name',     protocol.String),
        ('client_lang',     protocol.UInt8),
        ('join_date',       protocol.Date),
        ('client_play_as',  protocol.UInt8),
    ]


class ServerClientUpdatePacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CLIENT_UPDATE
    _fields = [
        ('client_id',       protocol.UInt32),
        ('client_name',     protocol.String),
        ('client_play_as',  protocol.UInt8),
    ]


class ServerClientQuitPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CLIENT_QUIT
    _fields = [
        ('client_id', protocol.UInt32),
    ]


class ServerClientErrorPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_CLIENT_QUIT
    _fields = [
        ('client_id',   protocol.UInt32),
        ('error',       protocol.UInt8),
    ]


class ServerCompanyNewPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_NEW
    _fields = [
        ('company_id', protocol.UInt8),
    ]


class ServerCompanyInfoPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_INFO
    _fields = [
        ('company_id',              protocol.UInt8),
        ('company_name',            protocol.String),
        ('manager_name',            protocol.String),
        ('colour',                  protocol.UInt8),
        ('is_passworded',           protocol.Boolean),
        ('inaugurated_year',        protocol.UInt32),  # Just the year
        ('is_ai',                   protocol.Boolean),
        ('months_of_bankruptcy',    protocol.UInt8),
        ('share_owners',            '_decode_share_owners'),
    ]

    def _decode_share_owners(self):
        """Share owners are appended at the end of the packet"""
        res = []
        share_owner_type = protocol.UInt8
        while (self.index + share_owner_type.struct.size) < len(self.raw_data):
            res.append(self._decode_field(share_owner_type))


class ServerCompanyUpdatePacket(ServerPacket):
    """Same fields as erverCompanyInfoPacket"""
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_UPDATE
    _fields = [
        ('company_id',              protocol.UInt8),
        ('company_name',            protocol.String),
        ('manager_name',            protocol.String),
        ('colour',                  protocol.UInt8),
        ('is_passworded',           protocol.Boolean),
        ('months_of_bankruptcy',    protocol.UInt8),
        ('share_owners',            '_decode_share_owners'),
    ]

    def _decode_share_owners(self):
        """Share owners are appended at the end of the packet"""
        res = []
        share_owner_type = protocol.UInt8
        while (self.index + share_owner_type.struct.size) < len(self.raw_data):
            res.append(self._decode_field(share_owner_type))


class ServerCompanyRemovePacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_REMOVE
    _fields = [
        ('company_id',    protocol.UInt8),
        ('remove_reason', protocol.UInt8),  # A value of AdminCompanyRemoveReason
    ]


class ServerCompanyEconomyPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_ECONOMY
    _fields = [
        ('company_id',              protocol.UInt8),
        ('money',                   protocol.SInt64),  # British Pound
        ('current_loan',            protocol.UInt64),
        ('income',                  protocol.SInt64),  # current year
        ('delivered_cargo',         protocol.UInt16),  # current quarter
        ('company_value_0',         protocol.UInt64),
        ('performance_history_0',   protocol.UInt16),
        ('delivered_cargo_0',       protocol.UInt16),
        ('company_value_1',         protocol.UInt64),
        ('performance_history_1',   protocol.UInt16),
        ('delivered_cargo_1',       protocol.UInt16),    
    ]


class ServerCompanyStatsPacket(ServerPacket):
    type_ = PacketTypes.ADMIN_PACKET_SERVER_COMPANY_STATS
    _fields = [
        ('company_id',              protocol.UInt8),
        ('train_vehicles_count',    protocol.UInt16),
        ('lorry_vehicles_count',    protocol.UInt16),
        ('bus_vehicles_count',      protocol.UInt16),
        ('plane_vehicles_count',    protocol.UInt16),
        ('ship_vehicles_count',     protocol.UInt16),
        ('train_stations_count',    protocol.UInt16),
        ('lorry_stations_count',    protocol.UInt16),
        ('bus_stations_count',      protocol.UInt16),
        ('plane_stations_count',    protocol.UInt16),
        ('ship_stations_count',     protocol.UInt16),
    ]


# maps packet type with class, makes sense only for server packets
packet_map = {
    PacketTypes.ADMIN_PACKET_ADMIN_JOIN: AdminJoinPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_QUIT: AdminQuitPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_UPDATE_FREQUENCY: AdminUpdateFrequenciesPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_POLL: AdminPollPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_CHAT: AdminChatPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_RCON: AdminRConPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_GAMESCRIPT: AdminGameScriptPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_PING: AdminPingPacket,
    PacketTypes.ADMIN_PACKET_SERVER_FULL: None,
    PacketTypes.ADMIN_PACKET_SERVER_BANNED: None,
    PacketTypes.ADMIN_PACKET_SERVER_ERROR: None,
    PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL: ServerProtocolPacket,
    PacketTypes.ADMIN_PACKET_SERVER_WELCOME: ServerWelcomePacket,
    PacketTypes.ADMIN_PACKET_SERVER_NEWGAME: None,
    PacketTypes.ADMIN_PACKET_SERVER_SHUTDOWN: None,
    PacketTypes.ADMIN_PACKET_SERVER_DATE: ServerDatePacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_JOIN: ServerClientJoinPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_INFO: ServerClientInfoPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_UPDATE: ServerClientUpdatePacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_QUIT: ServerClientQuitPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_ERROR: ServerClientErrorPacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_NEW: ServerCompanyNewPacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_INFO: ServerCompanyInfoPacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_UPDATE: ServerCompanyUpdatePacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_REMOVE: ServerCompanyRemovePacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_ECONOMY: ServerCompanyEconomyPacket,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_STATS: ServerCompanyStatsPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CHAT: ServerChatPacket,
    PacketTypes.ADMIN_PACKET_SERVER_RCON: ServerRConPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CONSOLE: None,
    PacketTypes.ADMIN_PACKET_SERVER_CMD_NAMES: None,
    PacketTypes.ADMIN_PACKET_SERVER_CMD_LOGGING: None,
    PacketTypes.ADMIN_PACKET_SERVER_GAMESCRIPT: ServerGameScriptPacket,
    PacketTypes.ADMIN_PACKET_SERVER_RCON_END: ServerRConEndPacket,
    PacketTypes.ADMIN_PACKET_SERVER_PONG: ServerPongPacket,
    PacketTypes.INVALID_ADMIN_PACKET: None,  # TODO Is this ever sent over the wire?
}
