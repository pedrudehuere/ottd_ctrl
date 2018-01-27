#!/usr/bin/python3.5
# -*- coding: utf-8 -*-

# standard library
from argparse import ArgumentParser
import logging

# project
from ottd_ctrl.const import AdminUpdateType as AUT, AdminUpdateFrequency as AUF
from ottd_ctrl.session import Session

WEBSITE = 'https://github.com/pedrudehuere/ottd_ctrl'
CLIENT_WELCOME_MSG = ['Welcome!',
                      'This server is powered by ottd_ctrl',
                      'For more information: ',
                      WEBSITE]


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('--server-password', required=True)
    ap.add_argument('--server-host', default='localhost')
    ap.add_argument('--server-port', default=3977)
    ap.add_argument('--verbose', action='store_true')
    return ap.parse_args()


if __name__ == '__main__':
    args = parse_args()

    if args.verbose:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    date_fmt = '%Y-%m-%d_%H:%M:%S'
    logging.basicConfig(filename=None, level=log_level, format=fmt, datefmt=date_fmt)
    log = logging.getLogger('ottd')
    log.info('start')

    # starting admin client
    session_kwargs = {
        'client_name': 'ottd_ctrl',
        'password': args.server_password,
        'client_version': '1',
        'server_host': args.server_host,
        'server_port': args.server_port,
        'timeout_s': 10,
        'client_welcome_message': CLIENT_WELCOME_MSG
    }
    with Session(**session_kwargs).quitting_server() as session:
        session.main_loop()

    log.info('end')
