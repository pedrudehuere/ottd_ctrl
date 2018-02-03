# -*- coding: utf-8 -*-

# standard library
from datetime import date
# related
import pytest
# project
from ottd_ctrl.packet import ServerDatePacket
from ottd_ctrl.protocol import Date
from ottd_ctrl.session import Session


def date_pkt(date):
    d = Date(value=date)
    pkt = ServerDatePacket(size=d.raw_size, raw_data=d.raw_data)
    pkt.magic_decode()
    return pkt


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
def test_new_day_callback(date_pkgs_called):

    packets, should_be_called = date_pkgs_called
    times_called = 0

    class TestSession(Session):
        def on_new_day(self, date):
            nonlocal times_called
            times_called += 1

    session = TestSession('name', 'passwd', 'version', 'host', 1000)

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
def test_new_month_callback(date_pkgs_called):

    packets, should_be_called = date_pkgs_called
    called = 0

    class TestSession(Session):
        def on_new_month(self, date):
            nonlocal called
            called += 1

    session = TestSession('name', 'passwd', 'version', 'host', 1000)

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
def test_new_year_callback(date_pkgs_called):

    packets, should_be_called = date_pkgs_called
    called = 0

    class TestSession(Session):
        def on_new_year(self, date):
            nonlocal called
            called += 1

    session = TestSession('name', 'passwd', 'version', 'host', 1000)

    for pkt in packets:
        session._on_date(pkt)

    assert called == should_be_called, \
        'on_new_year() callback has not been called' if should_be_called \
        else 'on_new_year() callback has wrongfully been called'
