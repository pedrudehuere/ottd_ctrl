#!/usr/bin/env python
# -*- coding: utf-8 -*-

from argparse import ArgumentParser
from distutils.dir_util import copy_tree  # like shutils.copytree() but copies content
import os.path
import shutil


openttd_base = 'openttd-1.7.2-linux-generic-amd64'
opengfx_files_dir = 'downloads/opengfx-0.5.2'
default_config_file = 'default_openttd.cfg'


def parse_args():
    ap = ArgumentParser()
    ap.add_argument('destination')
    ap.add_argument('--config-file', required=False)

    args = ap.parse_args()
    return args


def run(destination, config_file=None):
    # checking destination
    if os.path.exists(destination):
        raise Exception('{} exists'.format(destination))

    # making destination
    os.makedirs(destination)

    # copying config file
    if config_file is None:
        config_file = default_config_file
    shutil.copy(config_file, os.path.join(destination, 'openttd.cfg'))


if __name__ == '__main__':
    args = parse_args()
    run(**vars(args))
