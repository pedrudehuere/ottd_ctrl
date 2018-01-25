# -*- coding: utf-8 -*-

# standard library
from contextlib import contextmanager
import logging
import math
from select import select
import time

# project
from .admin_client import AdminClient, CallbackPrepend
from . import packet
from .const import AdminUpdateFrequencyStr, AdminUpdateTypeStr
from .const import PacketTypes
from .const import NetworkErrorCodeStr


class NotAllPacketReceived(Exception):
    pass


class Session(AdminClient):
    def __init__(self, client_name, password, client_version,
                 server_host, server_port,
                 timeout_s=None, callbacks=None, update_frequencies=None):
        super().__init__(server_host, server_port, timeout_s, callbacks)

        self.log = logging.getLogger('session')
        builtin_callbacks = {
            None:                                       (CallbackPrepend, [self._on_packet]),
            PacketTypes.ADMIN_PACKET_SERVER_WELCOME:    (CallbackPrepend, [self._on_welcome]),
            PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL:   (CallbackPrepend, [self._on_protocol]),
            PacketTypes.ADMIN_PACKET_SERVER_DATE:       (CallbackPrepend, [self._on_date]),
            PacketTypes.ADMIN_PACKET_SERVER_RCON:       (CallbackPrepend, [self._on_rcon]),
            PacketTypes.ADMIN_PACKET_SERVER_NEWGAME:    (CallbackPrepend, [self._on_new_game]),
            PacketTypes.ADMIN_PACKET_SERVER_SHUTDOWN:   (CallbackPrepend, [self._on_server_shutdown]),
            PacketTypes.ADMIN_PACKET_SERVER_CONSOLE:    (CallbackPrepend, [self._on_console]),
            PacketTypes.ADMIN_PACKET_SERVER_ERROR:      (CallbackPrepend, [self._on_server_error]),
            PacketTypes.ADMIN_PACKET_SERVER_CLIENT_JOIN:(CallbackPrepend, [self._on_client_join]),
            PacketTypes.ADMIN_PACKET_SERVER_CLIENT_INFO:(CallbackPrepend, [self._on_client_info]),
            PacketTypes.ADMIN_PACKET_SERVER_CLIENT_UPDATE: (CallbackPrepend, [self._on_client_update]),
            PacketTypes.ADMIN_PACKET_SERVER_CLIENT_QUIT: (CallbackPrepend, [self._on_client_quit]),
        }
        self._register_callbacks(builtin_callbacks)

        self.client_name = client_name
        self.password = password
        self.client_version = client_version
        self._update_frequencies = update_frequencies

        self.welcome_packet = None
        self.protocol_packet = None

        self.supported_update_frequencies = None

        self.stop = False
        self._server_joined = False
        self.current_date = None

        # Set when we send an rcon package
        self._current_rcon_request = None

        self.connected_clients = {}  # by client ID

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
        self.send_packet(packet.AdminJoinPacket(password=self.password,
                                                name=self.client_name,
                                                version=self.client_version))
        self.wait_for_packets(packet_types=[PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL,
                                            PacketTypes.ADMIN_PACKET_SERVER_WELCOME],
                              timeout_s=5)

        if self._server_joined:
            self.log.info("Server '%s' joined, protocol version: %s",
                     self.server_name, self.server_version)
        else:
            self.log.error("Could not jon server")

        # setting update frequencies
        self._set_update_frequencies(self._update_frequencies)

    def send_rcon(self, command, timeout_s=5):
        """
        Sends an rcon command, returns the result
        :param command:
        :return:
        """
        if self._current_rcon_request is not None:
            self.log.error('Sending RCON while RCON request in progress')
        pkt = packet.AdminRConPacket(command=command)
        self.send_packet(pkt)
        self._current_rcon_request = {
            'packet': pkt,
            'results': []
        }
        pkt = self.wait_for_packet(PacketTypes.ADMIN_PACKET_SERVER_RCON_END, timeout_s)
        self.log.debug("Result for RCON command '%s': ", command)
        for line in self._current_rcon_request['results']:
            self.log.info(line)
        results = self._current_rcon_request['results']
        self._current_rcon_request = None
        return results

    def set_update_frequency(self, update_type, update_frequency):
        """Checks if given frequency is supported by server, if not raises an error"""
        if self.supported_update_frequencies is not None:
            if update_type not in self.supported_update_frequencies:
                raise Exception('Unknown update type %s' % update_type)
            if not self.supported_update_frequencies[update_type] & update_frequency:
                raise Exception('Frequency %s not supported for type %s' %
                                (AdminUpdateFrequencyStr[update_frequency],
                                 AdminUpdateTypeStr[update_type]))
            self.send_packet(packet.AdminUpdateFrequenciesPacket(update_type=update_type,
                                                                 update_frequency=update_frequency))
        else:
            self.log.warning('Setting update frequencies without knowing supported frequencies')

    def main_loop(self):
        while not self.stop:
            self.receive_packets(timeout_s=5)

    def quit_server(self):
        self.send_packet(packet.AdminQuitPacket())
        self.disconnect()
        self._server_joined = False

    def wait_for_packet(self, packet_type, timeout_s=None):
        """
        Receives packets, returns once a packet of given type is received
        """
        remaining_s = timeout_s if timeout_s is not None else math.inf
        while remaining_s > 0:
            start_time = time.time()
            pkt = self.receive_packet()
            if pkt.type_ == packet_type:
                return packet
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
            self.log.debug('socket ready for read')
            self.receive_packet()
            nb_received += 1
            rlist, wlist, xlist = select([self.socket], [], [], timeout_s)
        if nb is not None and nb_received < nb:
            raise NotAllPacketReceived()
        self.log.debug('nothing to read')

    # we store data coming from server directly in the received packets
    @property
    def server_name(self):
        return self.welcome_packet.server_name if self.welcome_packet is not None else None

    @property
    def server_version(self):
        return self.protocol_packet.version if self.welcome_packet is not None else None

    # #### callback on packet reception ######################################
    def _on_packet(self, pkt):
        self.log.debug('Received %s: %s', pkt.__class__.__name__, pkt.pretty())

    def _on_welcome(self, pkt):
        self.welcome_packet = pkt
        self._server_joined = True

    def _on_protocol(self, pkt):
        self.protocol_packet = pkt
        self.supported_update_frequencies = pkt.supported_update_freqs

    def _on_date(self, pkt):
        self.current_date = pkt.date

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
        self.connected_clients[pkt.client_id] = None

    def _on_client_info(self, pkt):
        self.connected_clients[pkt.client_id] = pkt

    def _on_client_update(self, pkt):
        pass

    def _on_client_quit(self, pkt):
        try:
            del self.connected_clients[pkt.client_id]
        except KeyError:
            self.log.exception('Client that quit was unknown')

    def log_connected_clients(self):
        self.log.info('Connected clients: {}', self.connected_clients)
