# -*- coding: utf-8 -*-

# standard library
from enum import Enum
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


def enum_str(enum):
    """Returns a dict with strings by constant"""
    return {v: k for k, v in enum.__dict__.items() if not k.startswith('__')}


# src/network/core/tcp_admin.h
class PacketTypes:
    UNKNOWN_PACKET = -1

    ADMIN_PACKET_ADMIN_JOIN = 0                 # The admin announces and authenticates itself to the server.
    ADMIN_PACKET_ADMIN_QUIT = 1                 # The admin tells the server that it is quitting.
    ADMIN_PACKET_ADMIN_UPDATE_FREQUENCY = 2     # The admin tells the server the update frequency of a particular piece of information.
    ADMIN_PACKET_ADMIN_POLL = 3                 # The admin explicitly polls for a piece of information.
    ADMIN_PACKET_ADMIN_CHAT = 4                 # The admin sends a chat message to be distributed.
    ADMIN_PACKET_ADMIN_RCON = 5                 # The admin sends a remote console command.
    ADMIN_PACKET_ADMIN_GAMESCRIPT = 6           # The admin sends a JSON string for the GameScript.
    ADMIN_PACKET_ADMIN_PING = 7                 # The admin sends a ping to the server, expecting a ping-reply (PONG) packet.

    ADMIN_PACKET_SERVER_FULL = 100              # The server tells the admin it cannot accept the admin.
    ADMIN_PACKET_SERVER_BANNED = 101            # The server tells the admin it is banned.
    ADMIN_PACKET_SERVER_ERROR = 102             # The server tells the admin an error has occurred.
    ADMIN_PACKET_SERVER_PROTOCOL = 103          # The server tells the admin its protocol version.
    ADMIN_PACKET_SERVER_WELCOME = 104           # The server welcomes the admin to a game.
    ADMIN_PACKET_SERVER_NEWGAME = 105           # The server tells the admin its going to start a new game.
    ADMIN_PACKET_SERVER_SHUTDOWN = 106          # The server tells the admin its shutting down.

    ADMIN_PACKET_SERVER_DATE = 107              # The server tells the admin what the current game date is.
    ADMIN_PACKET_SERVER_CLIENT_JOIN = 108       # The server tells the admin that a client has joined.
    ADMIN_PACKET_SERVER_CLIENT_INFO = 109       # The server gives the admin information about a client.
    ADMIN_PACKET_SERVER_CLIENT_UPDATE = 110     # The server gives the admin an information update on a client.
    ADMIN_PACKET_SERVER_CLIENT_QUIT = 111       # The server tells the admin that a client quit.
    ADMIN_PACKET_SERVER_CLIENT_ERROR = 112      # The server tells the admin that a client caused an error.
    ADMIN_PACKET_SERVER_COMPANY_NEW = 113       # The server tells the admin that a new company has started.
    ADMIN_PACKET_SERVER_COMPANY_INFO = 114      # The server gives the admin information about a company.
    ADMIN_PACKET_SERVER_COMPANY_UPDATE = 115    # The server gives the admin an information update on a company.
    ADMIN_PACKET_SERVER_COMPANY_REMOVE = 116    # The server tells the admin that a company was removed.
    ADMIN_PACKET_SERVER_COMPANY_ECONOMY = 117   # The server gives the admin some economy related company information.
    ADMIN_PACKET_SERVER_COMPANY_STATS = 118     # The server gives the admin some statistics about a company.
    ADMIN_PACKET_SERVER_CHAT = 119              # The server received a chat message and relays it.
    ADMIN_PACKET_SERVER_RCON = 120              # The server's reply to a remove console command.
    ADMIN_PACKET_SERVER_CONSOLE = 121           # The server gives the admin the data that got printed to its console.
    ADMIN_PACKET_SERVER_CMD_NAMES = 122         # The server sends out the names of the DoCommands to the admins.
    ADMIN_PACKET_SERVER_CMD_LOGGING = 123       # The server gives the admin copies of incoming command packets.
    ADMIN_PACKET_SERVER_GAMESCRIPT = 124        # The server gives the admin information from the GameScript in JSON.
    ADMIN_PACKET_SERVER_RCON_END = 125          # The server indicates that the remote console command has completed.
    ADMIN_PACKET_SERVER_PONG = 126              # The server replies to a ping request from the admin.

    INVALID_ADMIN_PACKET = 0xFF,         # An invalid marker for admin packets.


# src/network/network_type.h
class DestType:
    DESTTYPE_BROADCAST = 0  # Send message/notice to all clients (All)
    DESTTYPE_TEAM = 1       # Send message/notice to everyone playing the same company (Team)
    DESTTYPE_CLIENT = 2     # Send message/notice to only a certain client (Private)


# src/network/network_type.h
class NetworkAction:
    NETWORK_ACTION_JOIN = 0
    NETWORK_ACTION_LEAVE = 1
    NETWORK_ACTION_SERVER_MESSAGE = 2
    NETWORK_ACTION_CHAT = 3
    NETWORK_ACTION_CHAT_COMPANY = 4
    NETWORK_ACTION_CHAT_CLIENT = 5
    NETWORK_ACTION_GIVE_MONEY = 6
    NETWORK_ACTION_NAME_CHANGE = 7
    NETWORK_ACTION_COMPANY_SPECTATOR = 8
    NETWORK_ACTION_COMPANY_JOIN = 9
    NETWORK_ACTION_COMPANY_NEW = 10


# Update types an admin can register a frequency for
# or poll manually
# src/network/core/tcp_admin.h
class AdminUpdateType:
    ADMIN_UPDATE_DATE = 0               # Updates about the date of the game.
    ADMIN_UPDATE_CLIENT_INFO = 1        # Updates about the information of clients.
    ADMIN_UPDATE_COMPANY_INFO = 2       # Updates about the generic information of companies.
    ADMIN_UPDATE_COMPANY_ECONOMY = 3    # Updates about the economy of companies.
    ADMIN_UPDATE_COMPANY_STATS = 4      # Updates about the statistics of companies.
    ADMIN_UPDATE_CHAT = 5               # The admin would like to have chat messages.
    ADMIN_UPDATE_CONSOLE = 6            # The admin would like to have console messages.
    ADMIN_UPDATE_CMD_NAMES = 7          # The admin would like a list of all DoCommand names.
    ADMIN_UPDATE_CMD_LOGGING = 8        # The admin would like to have DoCommand information.
    ADMIN_UPDATE_GAMESCRIPT = 9         # The admin would like to have gamescript messages.
    ADMIN_UPDATE_END = 10               # Must ALWAYS be on the end of this list!! (period)


# Update frequencies an admin can register
# src/network/core/tcp_admin.h
class AdminUpdateFrequency:
    ADMIN_FREQUENCY_POLL = 0x01         # The admin can poll this.
    ADMIN_FREQUENCY_DAILY = 0x02        # The admin gets information about this on a daily basis.
    ADMIN_FREQUENCY_WEEKLY = 0x04       # The admin gets information about this on a weekly basis.
    ADMIN_FREQUENCY_MONTHLY = 0x08      # The admin gets information about this on a monthly basis.
    ADMIN_FREQUENCY_QUARTERLY = 0x10    # The admin gets information about this on a quarterly basis.
    ADMIN_FREQUENCY_ANUALLY = 0x20      # The admin gets information about this on a yearly basis.
    ADMIN_FREQUENCY_AUTOMATIC = 0x40    # The admin gets information about this when it changes.


# src/network/network_type.h
class NetworkErrorCode:
    NETWORK_ERROR_GENERAL = 0  # Try to use this one like never

    # Signals from clients
    NETWORK_ERROR_DESYNC = 1
    NETWORK_ERROR_SAVEGAME_FAILED = 2
    NETWORK_ERROR_CONNECTION_LOST = 3
    NETWORK_ERROR_ILLEGAL_PACKET = 4
    NETWORK_ERROR_NEWGRF_MISMATCH = 5

    # Signals from servers
    NETWORK_ERROR_NOT_AUTHORIZED = 6
    NETWORK_ERROR_NOT_EXPECTED = 7
    NETWORK_ERROR_WRONG_REVISION = 8
    NETWORK_ERROR_NAME_IN_USE = 9
    NETWORK_ERROR_WRONG_PASSWORD = 10
    NETWORK_ERROR_COMPANY_MISMATCH = 11  # Happens in CLIENT_COMMAND
    NETWORK_ERROR_KICKED = 12
    NETWORK_ERROR_CHEATER = 13
    NETWORK_ERROR_FULL = 14
    NETWORK_ERROR_TOO_MANY_COMMANDS = 15
    NETWORK_ERROR_TIMEOUT_PASSWORD = 16
    NETWORK_ERROR_TIMEOUT_COMPUTER = 17
    NETWORK_ERROR_TIMEOUT_MAP = 18
    NETWORK_ERROR_TIMEOUT_JOIN = 19

    NETWORK_ERROR_END = 20


# String for constants
AdminUpdateTypeStr = enum_str(AdminUpdateType)
NetworkErrorCodeStr = enum_str(NetworkErrorCode)


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
                field = getattr(self, name)
                if field is None:
                    # we ignore None fields
                    # this works because None (or null) is not a valid value to send over the network
                    continue
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


# maps packet type with class, makes sense only for server packets
packet_map = {
    PacketTypes.ADMIN_PACKET_ADMIN_JOIN: AdminJoinPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_QUIT: None,
    PacketTypes.ADMIN_PACKET_ADMIN_UPDATE_FREQUENCY: None,
    PacketTypes.ADMIN_PACKET_ADMIN_POLL: AdminPollPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_CHAT: None,
    PacketTypes.ADMIN_PACKET_ADMIN_RCON: AdminRConPacket,
    PacketTypes.ADMIN_PACKET_ADMIN_GAMESCRIPT: None,
    PacketTypes.ADMIN_PACKET_ADMIN_PING: None,
    PacketTypes. ADMIN_PACKET_SERVER_FULL: None,
    PacketTypes.ADMIN_PACKET_SERVER_BANNED: None,
    PacketTypes.ADMIN_PACKET_SERVER_ERROR: None,
    PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL: ServerProtocolPacket,
    PacketTypes.ADMIN_PACKET_SERVER_WELCOME: ServerWelcomePacket,
    PacketTypes.ADMIN_PACKET_SERVER_NEWGAME: None,
    PacketTypes.ADMIN_PACKET_SERVER_SHUTDOWN: None,
    PacketTypes. ADMIN_PACKET_SERVER_DATE: ServerDatePacket,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_JOIN: None,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_INFO: None,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_UPDATE: None,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_QUIT: None,
    PacketTypes.ADMIN_PACKET_SERVER_CLIENT_ERROR: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_NEW: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_INFO: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_UPDATE: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_REMOVE: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_ECONOMY: None,
    PacketTypes.ADMIN_PACKET_SERVER_COMPANY_STATS: None,
    PacketTypes.ADMIN_PACKET_SERVER_CHAT: None,
    PacketTypes.ADMIN_PACKET_SERVER_RCON: ServerRConPacket,
    PacketTypes.ADMIN_PACKET_SERVER_CONSOLE: None,
    PacketTypes.ADMIN_PACKET_SERVER_CMD_NAMES: None,
    PacketTypes.ADMIN_PACKET_SERVER_CMD_LOGGING: None,
    PacketTypes.ADMIN_PACKET_SERVER_GAMESCRIPT: None,
    PacketTypes.ADMIN_PACKET_SERVER_RCON_END: ServerRConEndPacket,
    PacketTypes.ADMIN_PACKET_SERVER_PONG: None,
    PacketTypes. INVALID_ADMIN_PACKET: None,
}
