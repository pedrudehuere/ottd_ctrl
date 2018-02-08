# -*- coding: utf-8 -*-

# standard library
from datetime import date
# related
import pytest
# project
from ottd_ctrl.const import DestType, NetworkAction
from ottd_ctrl.packet import AdminChatPacket, AdminPacket, ServerDatePacket
from ottd_ctrl.protocol import Date
from ottd_ctrl.session import Session


dummy_session_args = ('name', 'pass', 1, 'host', 1)


def date_pkt(date):
    d = Date(value=date)
    pkt = ServerDatePacket(size=d.raw_size, raw_data=d.raw_data)
    pkt.magic_decode()
    return pkt


def chat_pkt(dest_type, dest, msg):
    return AdminChatPacket(network_action=NetworkAction.NETWORK_ACTION_CHAT,
                           destination_type=dest_type,
                           destination=dest,
                           message=msg)


class TestDateChangeCallbacks:
    """Testing date change callbacks on_new_day, on_new_month, on_new_year"""

    @pytest.mark.parametrize('date_pkgs_called', [
        ([date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 2)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 2))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 2, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 2)),
          date_pkt(date(1950, 1, 3))], 2),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 2)),
          date_pkt(date(1950, 1, 2))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 2, 1)),
          date_pkt(date(1950, 3, 1))], 2),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1)),
          date_pkt(date(1952, 1, 1))], 2)
    ])
    def test_new_day_callback(self, date_pkgs_called):

        packets, should_be_called = date_pkgs_called
        times_called = 0

        class NewDaySession(Session):
            def on_new_day(self, date):
                nonlocal times_called
                times_called += 1

        session = NewDaySession(*dummy_session_args)

        for pkt in packets:
            session._on_date(pkt)

        assert times_called == should_be_called, \
            'on_new_day() callback has been calles {} times, exptected: {}'.format(times_called,
                                                                                   should_be_called)

    @pytest.mark.parametrize('date_pkgs_called', [
        ([date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 2)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 2))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 2, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 2, 1)),
          date_pkt(date(1951, 1, 2))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 2, 1)),
          date_pkt(date(1950, 3, 1))], 2),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1)),
          date_pkt(date(1952, 1, 1))], 2),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 2, 1)),
          date_pkt(date(1951, 2, 1))], 1),
    ])
    def test_new_month_callback(self, date_pkgs_called):

        packets, should_be_called = date_pkgs_called
        called = 0

        class NewMonthSession(Session):
            def on_new_month(self, date):
                nonlocal called
                called += 1

        session = NewMonthSession(*dummy_session_args)

        for pkt in packets:
            session._on_date(pkt)

        assert called == should_be_called, \
            'on_new_month() callback has not been called' if should_be_called \
            else 'on_new_month() callback has wrongfully been called'

    @pytest.mark.parametrize('date_pkgs_called', [
        ([date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 2)),
          date_pkt(date(1950, 1, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 1, 2))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1950, 2, 1))], 0),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1)),
          date_pkt(date(1951, 2, 1))], 1),
        ([date_pkt(date(1950, 1, 1)),
          date_pkt(date(1951, 1, 1)),
          date_pkt(date(1952, 1, 1))], 2),
    ])
    def test_new_year_callback(self, date_pkgs_called):

        packets, should_be_called = date_pkgs_called
        called = 0

        class NewYearSession(Session):
            def on_new_year(self, date):
                nonlocal called
                called += 1

        session = NewYearSession(*dummy_session_args)

        for pkt in packets:
            session._on_date(pkt)

        assert called == should_be_called, \
            'on_new_year() callback has not been called' if should_be_called \
            else 'on_new_year() callback has wrongfully been called'


class TestSendChat:
    """Testing send_XXX_chat methods"""

    class MySession(Session):
        """Our session which overrides send_packet"""
        def __init__(self, expected_packets, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if isinstance(expected_packets, AdminChatPacket):
                expected_packets = [expected_packets]
            self.expected_packets = expected_packets
            self.sent_packets = []

        def send_packet(self, pkt):
            for attr in ('network_action',
                         'destination_type',
                         'destination',
                         'message'):
                assert getattr(pkt, attr) == \
                       getattr(self.expected_packets[len(self.sent_packets)], attr), \
                    'Chat packet attribute {} does not match'.format(attr)
            self.sent_packets.append(pkt)

    @pytest.mark.parametrize('attrs_expected', [
        ((2, 3, 'msg'), chat_pkt(2, 3, 'msg'))
    ])
    def test_send_chat(self, attrs_expected):
        (dest_type, dest, msg), expected_packet = attrs_expected
        s = self.MySession(expected_packet, *dummy_session_args)
        s._send_chat(dest_type, dest, msg)

    @pytest.mark.parametrize('attrs_expected', [
        ('miao', chat_pkt(dest_type=DestType.DESTTYPE_BROADCAST,
                          dest=0,
                          msg='miao')),
        (['miao'], chat_pkt(dest_type=DestType.DESTTYPE_BROADCAST,
                            dest=0,
                            msg='miao')),
        (['miao', 'bau'], (chat_pkt(dest_type=DestType.DESTTYPE_BROADCAST,
                                    dest=0,
                                    msg='miao'),
                           chat_pkt(dest_type=DestType.DESTTYPE_BROADCAST,
                                    dest=0,
                                    msg='bau')
                           )),
        ((), ()),
    ])
    def test_public_chat(self, attrs_expected):
        msg,  expected_packets = attrs_expected
        s = self.MySession(expected_packets, *dummy_session_args)
        s.send_public_chat(msg)

    @pytest.mark.parametrize('attrs_expected', [
        ((1, 'miao'), chat_pkt(dest_type=DestType.DESTTYPE_TEAM,
                               dest=1,
                               msg='miao')),
        ((1, ['miao']), chat_pkt(dest_type=DestType.DESTTYPE_TEAM,
                                 dest=1,
                                 msg='miao')),
        ((2, ['miao', 'bau']), (chat_pkt(dest_type=DestType.DESTTYPE_TEAM,
                                         dest=2,
                                         msg='miao'),
                                chat_pkt(dest_type=DestType.DESTTYPE_TEAM,
                                         dest=2,
                                         msg='bau'))),
        ((1, ()), ()),
    ])
    def test_send_company_chat(self, attrs_expected):
        (company_id, msg), expected_packets = attrs_expected
        s = self.MySession(expected_packets, *dummy_session_args)
        s.send_company_chat(msg, company_id)

    @pytest.mark.parametrize('attrs_expected', [
        ((1, 'miao'), chat_pkt(dest_type=DestType.DESTTYPE_CLIENT,
                               dest=1,
                               msg='miao')),
        ((1, ['miao']), chat_pkt(dest_type=DestType.DESTTYPE_CLIENT,
                                 dest=1,
                                 msg='miao')),
        ((2, ['miao', 'bau']), (chat_pkt(dest_type=DestType.DESTTYPE_CLIENT,
                                         dest=2,
                                         msg='miao'),
                                chat_pkt(dest_type=DestType.DESTTYPE_CLIENT,
                                         dest=2,
                                         msg='bau'))),
        ((1, ()), ()),
    ])
    def test_send_company_chat(self, attrs_expected):
        (company_id, msg), expected_packets = attrs_expected
        s = self.MySession(expected_packets, *dummy_session_args)
        s.send_client_chat(msg, company_id)