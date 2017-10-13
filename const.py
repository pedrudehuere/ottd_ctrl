# -*- coding: utf-8 -*-

"""
Constants
"""


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


# Reasons for removing a company - communicated to admins.
# src/network/tcp_admin.h
class AdminCompanyRemoveReason:
    ADMIN_CRR_MANUAL = 0     # The company is manually removed.
    ADMIN_CRR_AUTOCLEAN = 1  # The company is removed due to autoclean.
    ADMIN_CRR_BANKRUPT = 2   # The company went belly-up.
    ADMIN_CRR_END = 3        # Sentinel for end.


# Vehicletypes in the order they are send in info packets.
# src/network/network_type.h
class NetworkVehicleType:
    NETWORK_VEH_TRAIN = 0
    NETWORK_VEH_LORRY = 1
    NETWORK_VEH_BUS = 2
    NETWORK_VEH_PLANE = 3
    NETWORK_VEH_SHIP = 4
    NETWORK_VEH_END = 5


# String for constants
AdminUpdateTypeStr = enum_str(AdminUpdateType)
AdminUpdateFrequencyStr = enum_str(AdminUpdateFrequency)
NetworkErrorCodeStr = enum_str(NetworkErrorCode)
AdminCompanyRemoveReasonStr = enum_str(AdminCompanyRemoveReason)
NetworkVehicleTypeStr = enum_str(NetworkVehicleType)
PacketTypesStr = enum_str(PacketTypes)

