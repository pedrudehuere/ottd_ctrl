# -*- coding: utf-8 -*-


# standard library
from collections import defaultdict
from contextlib import contextmanager
import logging
import socket

# project
import packet

DEFAULT_SOCKET_TIMEOUT_S = 5


class CallbackPrepend:
    pass


class CallbackAppend:
    pass


class AdminClient:
    def __init__(self, server_host, server_port, timeout_s=None, callbacks=None):
        """

        :param server_host: Admin server host
        :param server_port: Admin server port
        """
        self.host = server_host
        self.port = server_port
        self.timeout_s = timeout_s or DEFAULT_SOCKET_TIMEOUT_S
        self.socket = None
        self.log = logging.getLogger("AdminClient")
        self.callbacks = defaultdict(list)
        self.register_callbacks(callbacks or {})

    def register_callbacks(self, callbacks):
        [[self.register_callback(pt, cb) for cb in cbs] for (pt, cbs) in callbacks.items()]

    def register_callback(self, packet_type, callback, position=None):
        if position is None:
            position = CallbackAppend
        if position is CallbackAppend:
            position = len(self.callbacks[packet_type])
        elif position is CallbackPrepend:
            position = 0
        self.callbacks[packet_type].insert(position, callback)

    @contextmanager
    def connected(self):
        self.connect()
        try:
            yield self
        finally:
            self.disconnect()

    def connect(self):
        self.socket = socket.create_connection((self.host, self.port))#, timeout=self.timeout_s)
        self.log.info("Connected to %s:%s", self.host, self.port)

    def disconnect(self):
        if self.socket is not None:
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.socket = None
            self.log.info("Disconnected")

    def send_packet(self, packet):
        if self.socket is None:
            raise Exception("Cannot send if not connected")
        # TODO handle socket errors
        self.socket.sendall(packet.encoded())

    def receive_packet(self):
        """Receives packet from network, calls registered callbacks"""
        if self.socket is None:
            raise Exception("Cannot receive if not connected")
        # reading packet size
        raw_size = self._read_bytes(packet.size_len)
        packet_size = packet.size_fmt.unpack(raw_size)[0]
        # reading bytes from socket
        raw_data = raw_size + self._read_bytes(packet_size - packet.size_len)
        # getting packet
        pkt = packet.ServerPacket.decode(packet_size, raw_data)
        # calling callbacks
        callbacks = self.callbacks.get(pkt.type_, [])
        for cb in callbacks:
            cb(pkt)
        return pkt

    def _receive_packet_size(self):
        return

    def _read_bytes(self, nb):
        """
        Reads given number of bytes and returns them
        """
        res = b''
        while nb > 0:
            recvd = self.socket.recv(nb)
            if recvd == '':
                # TODO investigate this case further
                raise Exception("Connecion closed")
            nb -= len(recvd)
            res += recvd
        return res
