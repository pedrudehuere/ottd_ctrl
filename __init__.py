#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

# standard library
from argparse import ArgumentParser
import os.path

# project
from const import AdminUpdateType, AdminUpdateFrequency
import log
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


# Date updates
update_freqs = {
    AdminUpdateType.ADMIN_UPDATE_DATE:              AdminUpdateFrequency.ADMIN_FREQUENCY_DAILY,
    AdminUpdateType.ADMIN_UPDATE_CLIENT_INFO:       AdminUpdateFrequency.ADMIN_FREQUENCY_AUTOMATIC,
    AdminUpdateType.ADMIN_UPDATE_COMPANY_INFO:      AdminUpdateFrequency.ADMIN_FREQUENCY_AUTOMATIC,
    AdminUpdateType.ADMIN_UPDATE_COMPANY_ECONOMY:   AdminUpdateFrequency.ADMIN_FREQUENCY_WEEKLY,
    AdminUpdateType.ADMIN_UPDATE_COMPANY_STATS:     AdminUpdateFrequency.ADMIN_FREQUENCY_WEEKLY,
    AdminUpdateType.ADMIN_UPDATE_CHAT:              AdminUpdateFrequency.ADMIN_FREQUENCY_AUTOMATIC,
    AdminUpdateType.ADMIN_UPDATE_CONSOLE:           AdminUpdateFrequency.ADMIN_FREQUENCY_AUTOMATIC,
}

if __name__ == '__main__':
    args = parse_args()
    log.init()

    log.info("Start")

    paths = Paths(args.base_path)

    # starting OpenTTD server
    with server.OpenTTDServer().stopping() as ottd_server:
        # starting admin client
        session_kwargs = {
            'client_name': 'ottd_ctrl',
            'password': 'pass',
            'client_version': '1',
            'server_host': 'localhost',
            'server_port': 3977,
            'timeout_s': 10,
            'update_frequencies': update_freqs,
        }
        with Session(**session_kwargs).quitting_server() as session:
            session.main_loop()

    log.info("End")
