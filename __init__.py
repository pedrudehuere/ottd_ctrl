#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

# standard library
from argparse import ArgumentParser
import os.path
import time

# project
import log
import packet
import server
from session import Session

paths = None


class Paths:
    """
    Contains all paths
    """
    def __init__(self, base_path):
        """
        :param base_path: where openttd is installed
        """
        self.base = base_path
        self.config_file = os.path.join(self.base, 'openttd.cfg')
        self.ottd_exec = os.path.join(self.base, 'openttd')
        # Adding openttd base path to PATH
        if base_path not in os.environ['PATH']:
            os.environ['PATH'] = os.path.join(os.environ['PATH'], base_path)


def parse_args():
    """
    Parses command line arguments
    """
    ap = ArgumentParser()
    ap.add_argument('--base-path', required=True, help="OpenTTD installation path")
    return ap.parse_args()


def on_welcome(pkt):
    log.info("Received welcome from server '%s'", pkt.server_name)


def on_protocol(pkt):
    log.info('Received protocol from server')


if __name__ == '__main__':
    args = parse_args()
    log.init()

    log.info("Start")

    paths = Paths(args.base_path)

    # starting OpenTTD server
    with server.OpenTTDServer().started() as ottd_server:
        # starting admin client
        session_kwargs = {
            'client_name': 'ottd_ctrl',
            'password': 'pass',
            'client_version': '1',
            'server_host': 'localhost',
            'server_port': 3977,
            'timeout_s': 10
        }
        with Session(**session_kwargs).server_joined() as session:

            # registering callbacks
            session.admin_client.register_callback(packet.PacketTypes.ADMIN_PACKET_SERVER_WELCOME,
                                                   on_welcome)
            session.admin_client.register_callback(packet.PacketTypes.ADMIN_PACKET_SERVER_PROTOCOL,
                                                   on_protocol)


            log.info("Working...")
            time.sleep(2)

            log.info("Asking for date")

            session.send_packet(packet.AdminPollPacket(update_type=packet.AdminUpdateType.ADMIN_UPDATE_DATE))
            the_date = session.receive_packet().date

            log.info('The date is: %s', the_date.strftime('%Y.%m.%d'))

    log.info("End")
