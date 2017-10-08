# -*- coding: utf-8 -*-

# standard library
from contextlib import contextmanager

# project
from admin_client import AdminClient, CallbackPrepend
import log
import packet
from packet import PacketTypes


class Session:
    def __init__(self, client_name, password, client_version,
                 server_host, server_port, timeout_s=None):
        self.client_name = client_name
        self.password = password
        self.client_version = client_version

        self.admin_client = AdminClient(server_host, server_port, timeout_s)

        self.welcome_packet = None
        self.protocol_packet = None

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
        self.receive_packet()  # protocol
        self.receive_packet()  # welcome
        log.info("Server '%s' joined, version: %s", self.server_name, self.server_version)

    def quit_server(self):
        self.send_packet(packet.AdminQuitPacket())
        self.admin_client.disconnect()

    def send_packet(self, pkt):
        log.info('Sending %s', pkt.__class__.__name__)
        self.admin_client.send_packet(pkt)

    def receive_packet(self):
        return self.admin_client.receive_packet()

    def _register_callbacks(self):
        callbacks = {
            None: self._on_packet,
            PacketTypes.ADMIN_PACKET_SERVER_WELCOME: self._on_welcome,
            PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL: self._on_protocol,
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
        log.info('Received %s', pkt.__class__.__name__)

    def _on_welcome(self, pkt):
        self.welcome_packet = pkt

    def _on_protocol(self, pkt):
        self.protocol_packet = pkt
