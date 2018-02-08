# -*- coding: utf-8 -*-

# standard library
from collections import defaultdict
from contextlib import contextmanager
import logging
import socket

# project
from ottd_ctrl.const import PacketTypesStr
from ottd_ctrl import packet

DEFAULT_SOCKET_TIMEOUT_S = 5


class CallbackPrepend:
    """Used for callback registration, callback will inserted at the beginning"""


class CallbackAppend:
    """Used for callback registration, callback will inserted at the end"""


class ConnectionClosedByPeer(Exception):
    pass


class AdminClient:
    def __init__(self, server_host, server_port, timeout_s=None, callbacks=None):
        """

        :param server_host: Admin server host
        :param server_port: Admin server port
        """
        self.host = server_host
        self.port = server_port
        self.timeout_s = timeout_s if timeout_s is not None else DEFAULT_SOCKET_TIMEOUT_S
        self.socket = None
        self.log = logging.getLogger("admin-client")
        self.log.setLevel(logging.DEBUG)
        self.callbacks = defaultdict(list)
        self.register_callbacks(callbacks or {})

    def register_callbacks(self, callbacks, position=CallbackAppend):
        """
        Registers callbacks for received packets
        :param callbacks: {pkt_type: [callback, ...], ...}
        :param position: Position in which insert callbacks in the call list,
                         an integer or one of CallbackPrepend, CallbackAppend
        """
        for packet_type, callback in callbacks.items():
            self.register_callback(packet_type, callback, position)

    def register_callback(self, packet_type, callback, position=CallbackAppend):
        """
        Registers callbacks for a given packet type
        :param packet_type: A PacketType const.PacketTypes
        :param callback: A callable with a packet as only argument
        :param position: An integer or one of CallbackAppend, CallbackPrepend
        """
        if position is CallbackAppend:
            position = len(self.callbacks[packet_type])
        elif position is CallbackPrepend:
            position = 0
        if isinstance(callback, (tuple, list)):
            self.callbacks[packet_type] = (self.callbacks[packet_type][:position] +
                                           list(callback) +
                                           self.callbacks[packet_type][position:])
        else:
            self.callbacks[packet_type].insert(position, callback)

    @property
    def is_connected(self):
        return self.socket is not None

    @contextmanager
    def connected(self):
        self.connect()
        try:
            yield self
        finally:
            self.disconnect()

    def connect(self):
        self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout_s)
        self.log.info("Connected to %s:%s", self.host, self.port)

    def disconnect(self):
        if self.socket is not None:
            try:
                # if the server already disconnected we have Errno 107
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError as e:
                self.log.error('Disconnecting: %s', e)
            self.socket.close()
            self.socket = None
            self.log.info("Disconnected")

    def send_packet(self, pkt):
        self.log.debug('Sending %s', pkt.__class__.__name__)
        if self.socket is None:
            raise Exception("Cannot send if not connected")
        # TODO handle socket errors
        self.socket.sendall(pkt.encoded())

    def receive_packet(self):
        """Receives packet from network, calls registered callbacks"""
        if self.socket is None:
            raise Exception("Cannot receive if not connected")
        # reading packet size
        try:
            raw_size = self._read_bytes(packet.size_len)
            packet_size = packet.size_fmt.unpack(raw_size)[0]
            # reading bytes from socket
            raw_data = raw_size + self._read_bytes(packet_size - packet.size_len)
        except ConnectionClosedByPeer:
            self.socket = None
            raise
        # getting packet
        pkt = packet.ServerPacket.decode(packet_size, raw_data)
        # calling generic callbacks (for all received packets)
        generic_callbacks = self.callbacks.get(None, [])
        for cb in generic_callbacks:
            self._call_callback(cb, pkt)
        # callbacks for specific packet
        callbacks = self.callbacks.get(pkt.type_, [])
        if len(callbacks) == 0:
            self.log.warning('No callback for packet type %s', PacketTypesStr[pkt.type_])
        for cb in callbacks:
            self._call_callback(cb, pkt)
        return pkt

    def _read_bytes(self, nb):
        """
        Reads given number of bytes and returns them
        """
        res = b''
        while nb > 0:
            recvd = self.socket.recv(nb)
            if len(recvd) == 0:
                # TODO investigate this case further
                raise ConnectionClosedByPeer()
            nb -= len(recvd)
            res += recvd
        return res

    def _call_callback(self, cb, *args, **kwargs):
        """Calls callback"""
        try:
            cb(*args, **kwargs)
        except Exception as e:
            args_str = ','.join(repr(a) for a in args)
            kwargs_str = ','.join('{}={}'.format(k, repr(v)) for k, v in kwargs.items())
            args_kwargs_str = ','.join([e for e in (args_str, kwargs_str) if e != ''])
            cb_str = '{}({})'.format(cb.__name__, args_kwargs_str)
            self.log.exception('Error while executing callback %s', cb_str)
