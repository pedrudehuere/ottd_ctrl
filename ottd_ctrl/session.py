# -*- coding: utf-8 -*-

# standard library
from contextlib import contextmanager
import math
from select import select
import time

# project
from .admin_client import AdminClient, CallbackPrepend
from .packet import *
from .const import AdminUpdateFrequencyStr, AdminUpdateTypeStr
from .const import DestType, PacketTypes as PT
from .const import NetworkAction, NetworkErrorCodeStr


class NotAllPacketReceived(Exception):
    pass


class Session(AdminClient):
    def __init__(self,
                 client_name,
                 password,
                 client_version,
                 server_host,
                 server_port,
                 timeout_s=None,
                 update_frequencies=None,
                 client_welcome_message=None):
        """
        A convenience class which inherits from AdminClient,
        keeps track of some data such as the current date and provides helper
        methods and callbacks
        :param client_name: Name of the admin client
        :param password: Password of the admin server
        :param client_version: Client version
        :param server_host: Host of the admin server
        :param server_port: Port of the admin server
        :param timeout_s: Timeout for socket operations
        :param update_frequencies: {AdminUpdateType: AdminUpdateFrequency, ...}
        :param client_welcome_message: A message which will be sent to a connected client,
                                       string or sequence of strings
        """
        super().__init__(server_host, server_port, timeout_s)

        self.log = logging.getLogger('session')

        self._update_frequencies = update_frequencies or {}

        self._pkt_callbacks = {
            None:                                   [self._on_packet, self.on_packet],
            PT.ADMIN_PACKET_SERVER_WELCOME:         [self._on_welcome, self.on_welcome],
            PT.ADMIN_PACKET_SERVER_PROTOCOL:        [self._on_protocol, self.on_protocol],
            PT.ADMIN_PACKET_SERVER_DATE:            [self._on_date, self.on_date],
            PT.ADMIN_PACKET_SERVER_RCON:            [self._on_rcon, self.on_rcon],
            PT.ADMIN_PACKET_SERVER_NEWGAME:         [self._on_new_game, self.on_new_game],
            PT.ADMIN_PACKET_SERVER_SHUTDOWN:        [self._on_server_shutdown, self.on_server_shutdown],
            PT.ADMIN_PACKET_SERVER_CONSOLE:         [self._on_console, self.on_console],
            PT.ADMIN_PACKET_SERVER_ERROR:           [self._on_server_error, self.on_server_error],
            PT.ADMIN_PACKET_SERVER_CLIENT_JOIN:     [self._on_client_join, self.on_client_join],
            PT.ADMIN_PACKET_SERVER_CLIENT_INFO:     [self._on_client_info, self.on_client_info],
            PT.ADMIN_PACKET_SERVER_CLIENT_UPDATE:   [self._on_client_update, self.on_client_update],
            PT.ADMIN_PACKET_SERVER_CLIENT_QUIT:     [self._on_client_quit, self.on_client_quit],
            PT.ADMIN_PACKET_SERVER_COMPANY_NEW:     self.on_company_new,
            PT.ADMIN_PACKET_SERVER_COMPANY_UPDATE:  self.on_company_update,
            PT.ADMIN_PACKET_SERVER_COMPANY_INFO:    self.on_company_info,
            PT.ADMIN_PACKET_SERVER_COMPANY_ECONOMY: self.on_company_economy,
            PT.ADMIN_PACKET_SERVER_COMPANY_STATS:   self.on_company_stats,
            PT.ADMIN_PACKET_SERVER_CHAT:            [self._on_chat, self.on_chat],
        }
        self.register_callbacks(self._pkt_callbacks, position=CallbackPrepend)

        self.client_name = client_name
        self.password = password
        self.client_version = client_version
        self.client_welcome_message = client_welcome_message

        self.welcome_packet = None
        self.protocol_packet = None

        self.supported_update_frequencies = None

        self.stop = False
        self._server_joined = False

        self.last_received_date = None
        self.current_date = None

        # Set when we send an rcon package
        self._current_rcon_request = None

    def _format_company_welcome_msg(self):
        if not isinstance(self.client_welcome_message, (list, tuple)):
            message = list(self.client_welcome_message)
        else:
            message = self.client_welcome_message
        return ['-' * 20] + list(message) + ['-' * 20]

    def _set_update_frequencies(self, update_frequencies):
        [self.set_update_frequency(*u_type_freq) for u_type_freq in update_frequencies.items()]

    @contextmanager
    def quitting_server(self):
        self.join_server()
        try:
            yield self
        finally:
            self.quit_server()

    def join_server(self):
        if self.is_connected:
            raise Exception('Already connected to server')
        self.connect()
        self.send_packet(AdminJoinPacket(password=self.password,
                                         name=self.client_name,
                                         version=self.client_version))
        self.wait_for_packets(packet_types=[PT.ADMIN_PACKET_SERVER_PROTOCOL,
                                            PT.ADMIN_PACKET_SERVER_WELCOME],
                              timeout_s=5)

        if self._server_joined:
            self.log.info("Joined server '%s', protocol version: %s",
                          self.server_name, self.server_version)
        else:
            self.log.error("Could not jon server")

        if self._update_frequencies:
            self._set_update_frequencies(self._update_frequencies)

        self.on_server_joined()

    def send_rcon(self, command, timeout_s=5):
        """
        Sends an rcon command, returns the result
        :param command:
        :return:
        """
        if self._current_rcon_request is not None:
            self.log.error('Sending RCON while RCON request in progress')
        pkt = AdminRConPacket(command=command)
        self.send_packet(pkt)
        self._current_rcon_request = {
            'packet': pkt,
            'results': []
        }
        pkt = self.wait_for_packet(PT.ADMIN_PACKET_SERVER_RCON_END, timeout_s)
        self.log.debug("Result for RCON command '%s': ", command)
        for line in self._current_rcon_request['results']:
            self.log.info(line)
        results = self._current_rcon_request['results']
        self._current_rcon_request = None
        return results

    def send_public_chat(self, message):
        """
        Sends a public chat message
        :param message: A string or sequence of strings,
                       if sequence every element is a different message
                       TODO I'm not really sure if it is possible to send
                            a chat message with line breaks, so for the moment the only
                            way to send multi line messages is to send one message
                            per line
        """
        if not isinstance(message, str):
            for line in message:
                self._send_chat(DestType.DESTTYPE_BROADCAST, 0, line)
        else:
            self._send_chat(DestType.DESTTYPE_BROADCAST, 0, message)

    def send_company_chat(self, message, company_id):
        """
        Sends a chat message to a given company
        :param message: A string or sequence of strings,
                        if sequence every element is a different message
        """
        if not isinstance(message, str):
            for line in message:
                self._send_chat(DestType.DESTTYPE_TEAM, company_id, line)
        else:
            self._send_chat(DestType.DESTTYPE_TEAM, company_id, message)

    def send_client_chat(self, message, client_id):
        """
        Sends chat message to a given client
        :param message: A string or sequence of strings,
                        if sequence every element is a different message
        """
        if not isinstance(message, str):
            for line in message:
                self._send_chat(DestType.DESTTYPE_CLIENT, client_id, line)
        else:
            self._send_chat(DestType.DESTTYPE_CLIENT, client_id, message)

    def _send_chat(self, dest_type, dest, message):
        """
        Sends a chat message
        :param dest_type: DestType
        :param dest: Destination, company_id, client_id or 0
        :param message: A string
        """
        self.send_packet(AdminChatPacket(network_action=NetworkAction.NETWORK_ACTION_CHAT,
                                         destination_type=dest_type,
                                         destination=dest,
                                         message=message))

    def set_update_frequency(self, update_type, update_frequency):
        """Checks if given frequency is supported by server, if not raises an error"""
        if self.supported_update_frequencies is not None:
            if update_type not in self.supported_update_frequencies:
                raise Exception('Unknown update type %s' % update_type)
            if not self.supported_update_frequencies[update_type] & update_frequency:
                raise Exception('Frequency %s not supported for type %s' %
                                (AdminUpdateFrequencyStr[update_frequency],
                                 AdminUpdateTypeStr[update_type]))
            self.send_packet(AdminUpdateFrequenciesPacket(update_type=update_type,
                                                          update_frequency=update_frequency))
        else:
            self.log.warning('Setting update frequencies without knowing supported frequencies')

    def main_loop(self):
        while not self.stop:
            self.receive_packets(timeout_s=5)

    def quit_server(self):
        self.send_packet(AdminQuitPacket())
        self.disconnect()
        self._server_joined = False
        self.on_server_quit()

    def wait_for_packet(self, packet_type, timeout_s=None):
        """
        Receives packets, returns once a packet of given type is received
        """
        remaining_s = timeout_s if timeout_s is not None else math.inf
        while remaining_s > 0:
            start_time = time.time()
            pkt = self.receive_packet()
            if pkt.type_ == packet_type:
                return pkt
            elapsed_s = time.time() - start_time
            remaining_s -= elapsed_s
        else:
            raise TimeoutError()

    def wait_for_packets(self, packet_types, timeout_s=None):
        """
        Waits until at least one of each packet types have been received
        """
        received_packets = {}
        packets_to_receive = set(packet_types)
        remaining_s = timeout_s if timeout_s is not None else math.inf
        while remaining_s > 0:
            pkt = self.receive_packet()
            packet_type = pkt.type_
            packets_to_receive.discard(packet_type)
            if packet_type in packet_types:
                received_packets.setdefault(packet_type, []).append(pkt)
            if len(packets_to_receive) == 0:
                return received_packets
        else:
            raise TimeoutError()

    def receive_packets(self, nb=None, timeout_s=0):
        """
        Receives packets if there are some
        :param timeout_s: Timeout in seconds for receiving each packet
        :param nb: Number of packets to receive, if None we just receive what's there
        """
        self.log.debug('receiving packets')
        nb_received = 0
        rlist, wlist, xlist = select([self.socket], [], [], timeout_s)
        while len(rlist) > 0 and not self.stop:
            if nb is not None and nb_received >= nb:
                break
            self.receive_packet()
            nb_received += 1
            rlist, wlist, xlist = select([self.socket], [], [], timeout_s)
        if nb is not None and nb_received < nb:
            raise NotAllPacketReceived()

    # we store data coming from server directly in the received packets
    @property
    def server_name(self):
        return self.welcome_packet.server_name if self.welcome_packet is not None else None

    @property
    def server_version(self):
        return self.protocol_packet.version if self.welcome_packet is not None else None

    # #### private callback on packet reception ######################################
    # #### these are not supposed to ne overridden
    def _on_packet(self, pkt):
        self.log.debug('Received %s', str(pkt))

    def _on_welcome(self, pkt):
        self.welcome_packet = pkt
        self._server_joined = True

    def _on_protocol(self, pkt):
        self.protocol_packet = pkt
        self.supported_update_frequencies = pkt.supported_update_freqs

    def _on_date(self, pkt):
        self.current_date = pkt.date
        if self.last_received_date is not None:
            if self.last_received_date.year < self.current_date.year:
                self.on_new_year(self.current_date)
                self.on_new_month(self.current_date)
                self.on_new_day(self.current_date)

            elif self.last_received_date.month < self.current_date.month:
                self.on_new_month(self.current_date)
                self.on_new_day(self.current_date)

            elif self.last_received_date.day < self.current_date.day:
                self.on_new_day(self.current_date)

        self.last_received_date = self.current_date

    def _on_rcon(self, pkt):
        if self._current_rcon_request is None:
            self.log.error('Received unexpected rcon result')
        else:
            # TODO colour
            self._current_rcon_request['results'].append(pkt.result)

    def _on_console(self, pkt):
        self.log.debug('Origin: %s, string: %s', pkt.origin, pkt.string)

    def _on_new_game(self, pkt):
        self.log.info('New game')

    def _on_server_shutdown(self, pkt):
        self.stop = True
        self.log.info('Server shutdown')

    def _on_server_error(self, pkt):
        self.log.info('Error: %s', NetworkErrorCodeStr[pkt.error])

    def _on_client_join(self, pkt):
        # sending a welcome message if set
        if self.client_welcome_message:
            for line in self._format_company_welcome_msg():
                self.send_packet(AdminChatPacket(network_action=NetworkAction.NETWORK_ACTION_CHAT_CLIENT,
                                                 destination_type=DestType.DESTTYPE_CLIENT,
                                                 destination=pkt.client_id,
                                                 message=line))

    def _on_client_info(self, pkt):
        pass

    def _on_client_update(self, pkt):
        pass

    def _on_client_quit(self, pkt):
        pass

    def _on_chat(self, pkt):
        pass

    # #### public callbacks, these can be overridden #########################
    # ## server connection ###################################################
    def on_server_joined(self):
        pass

    def on_server_quit(self):
        pass

    # ## packet callbacks ####################################################
    def on_packet(self, pkt):
        pass

    def on_welcome(self, pkt):
        pass

    def on_protocol(self, pkt):
        pass

    def on_date(self, date):
        pass

    def on_new_day(self, date):
        pass

    def on_new_month(self, date):
        pass

    def on_new_year(self, date):
        pass

    def on_rcon(self, pkt):
        pass

    def on_console(self, pkt):
        pass

    def on_new_game(self, pkt):
        pass

    def on_server_shutdown(self, pkt):
        pass

    def on_server_error(self, pkt):
        pass

    def on_client_join(self, pkt):
        pass

    def on_client_info(self, pkt):
        pass

    def on_client_update(self, pkt):
        pass

    def on_client_quit(self, pkt):
        pass

    def on_company_new(self, pkt):
        pass

    def on_company_update(self, pkt):
        pass

    def on_company_info(self, pkt):
        pass

    def on_company_economy(self, pkt):
        pass

    def on_company_stats(self, pkt):
        pass

    def on_chat(self, pkt):
        pass

