#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

# standard library
from argparse import ArgumentParser
import os.path
import time

# project
from admin_client import AdminClient
import packet
import server
import log

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


if __name__ == '__main__':
    args = parse_args()
    log.init()

    log.info("Start")

    paths = Paths(args.base_path)

    # starting OpenTTD server
    with server.OpenTTDServer().started() as ottd_server:
        # starting admin client
        with AdminClient('127.0.0.1', 3977, timeout_s=10).connected() as client:

            # sending Join packet
            join_packet = packet.AdminJoin('test', 'pass', '1.2.3')
            client.send_packet(join_packet)
            p1 = client.receive_packet()  # protocol
            p2 = client.receive_packet()  # welcome

            log.info("Working...")
            time.sleep(7)

    log.info("End")
