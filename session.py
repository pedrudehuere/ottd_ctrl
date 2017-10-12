# -*- coding: utf-8 -*-

# standard library
from contextlib import contextmanager
from time import sleep
from select import select

# project
from admin_client import AdminClient, CallbackPrepend
import log
import packet
from packet import PacketTypes, AdminUpdateType, AdminUpdateFrequency


class NotAllPacketReceived(Exception):
    pass


class Session:
    def __init__(self, client_name, password, client_version,
                 server_host, server_port, timeout_s=None):
        self.client_name = client_name
        self.password = password
        self.client_version = client_version

        self.admin_client = AdminClient(server_host, server_port, timeout_s)

        self.welcome_packet = None
        self.protocol_packet = None

        self._server_joined = False
        self.current_date = None

        self._register_callbacks()

    @contextmanager
    def server_joined(self):
        self.join_server()
        try:
            yield self
        finally:
            self.quit_server()

    def join_server(self):
        if self.admin_client.is_connected:
            raise Exception('Already connected to server')
        self.admin_client.connect()
        self.send_packet(packet.AdminJoinPacket(password=self.password,
                                                name=self.client_name,
                                                version=self.client_version))
        self.receive_packets(2, timeout_s=2)

        if self._server_joined:
            log.info("Server '%s' joined, version: %s", self.server_name, self.server_version)
        else:
            log.error("Could not jon server")

        self.send_packet(packet.AdminUpdateFrequenciesPacket(update_type=AdminUpdateType.ADMIN_UPDATE_DATE,
                                                             update_frequency=AdminUpdateFrequency.ADMIN_FREQUENCY_DAILY))

        # TODO send update frequencies

    def main_loop(self):
        stop = False
        while not stop:
            self.receive_packets(timeout_s=5)

    def quit_server(self):
        self.send_packet(packet.AdminQuitPacket())
        self.admin_client.disconnect()
        self._server_joined = False

    def send_packet(self, pkt):
        log.info('Sending %s', pkt.__class__.__name__)
        self.admin_client.send_packet(pkt)

    def receive_packet(self):
        # TODO capture ConnectionClosedByPeer
        return self.admin_client.receive_packet()

    def receive_packets(self, nb=None, timeout_s=0):
        """
        Receives packets if there are some
        :param timeout_s: Timeout in seconds for receiving each packet
        :param nb: Number of packets to receive, if None we just receive what's there
        """
        log.debug('receiving packets')
        nb_received = 0
        rlist, wlist, xlist = select([self.admin_client.socket], [], [], timeout_s)
        while len(rlist) > 0:
            if nb is not None and nb_received >= nb:
                break
            log.debug('socket ready for read')
            self.receive_packet()
            nb_received += 1
            rlist, wlist, xlist = select([self.admin_client.socket], [], [], timeout_s)
        if nb is not None and nb_received < nb:
            raise NotAllPacketReceived()
        log.debug('nothing to read')

    def _register_callbacks(self):
        callbacks = {
            None: self._on_packet,
            PacketTypes.ADMIN_PACKET_SERVER_WELCOME: self._on_welcome,
            PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL: self._on_protocol,
            PacketTypes.ADMIN_PACKET_SERVER_DATE: self._on_date,
        }
        for packet_type, callback in callbacks.items():
            self.admin_client.register_callback(packet_type, callback, CallbackPrepend)

    # we store data coming from server directly in the received packets
    @property
    def server_name(self):
        return self.welcome_packet.server_name if self.welcome_packet is not None else None

    @property
    def server_version(self):
        return self.protocol_packet.version if self.welcome_packet is not None else None

    # #### callback on packet reception ######################################
    def _on_packet(self, pkt):
        log.debug('Received %s: %s', pkt.__class__.__name__, pkt.pretty())

    def _on_welcome(self, pkt):
        self.welcome_packet = pkt
        self._server_joined = True

    def _on_protocol(self, pkt):
        self.protocol_packet = pkt

    def _on_date(self, pkt):
        self.current_date = pkt.date
