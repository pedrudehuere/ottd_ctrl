#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

# standard library
from argparse import ArgumentParser
import logging
import os.path

# project
from ottd_ctrl.const import AdminUpdateType as AUT, AdminUpdateFrequency as AUF
from ottd_ctrl.session import Session

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
    AUT.ADMIN_UPDATE_DATE:              AUF.ADMIN_FREQUENCY_DAILY,
    AUT.ADMIN_UPDATE_CLIENT_INFO:       AUF.ADMIN_FREQUENCY_AUTOMATIC,
    AUT.ADMIN_UPDATE_COMPANY_INFO:      AUF.ADMIN_FREQUENCY_AUTOMATIC,
    AUT.ADMIN_UPDATE_COMPANY_ECONOMY:   AUF.ADMIN_FREQUENCY_WEEKLY,
    AUT.ADMIN_UPDATE_COMPANY_STATS:     AUF.ADMIN_FREQUENCY_WEEKLY,
    AUT.ADMIN_UPDATE_CHAT:              AUF.ADMIN_FREQUENCY_AUTOMATIC,
    AUT.ADMIN_UPDATE_CONSOLE:           AUF.ADMIN_FREQUENCY_AUTOMATIC,
}

if __name__ == '__main__':
    args = parse_args()

    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    date_fmt = '%Y-%m-%d_%H:%M:%S'
    logging.basicConfig(filename=None, level=logging.DEBUG, format=fmt, datefmt=date_fmt)
    logging.getLogger('sh').setLevel(logging.INFO)
    log = logging.getLogger('ottd')
    log.info('start')

    paths = Paths(args.base_path)

    # starting OpenTTD server
    config_file = '/home/andrea/ottd_servers/1/openttd.cfg'
    # with server.OpenTTDServer(config_file=config_file).stopping() as ottd_server:


    # starting admin client
    session_kwargs = {
        'client_name': 'ottd_ctrl',
        'password': '7501',
        'client_version': '1',
        'server_host': '192.168.1.11',
        'server_port': 3977,
        'timeout_s': 10,
        'update_frequencies': update_freqs,
    }
    with Session(**session_kwargs).quitting_server() as session:
        session.main_loop()

    log.info('end')
