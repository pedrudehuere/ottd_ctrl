# -*- coding:utf8 -*-

# standard
import logging

ottd_ctrl_logger = None
debug = None
info = None
warning = None
error = None
exception = None


def init(name='ottd_ctrl', level=logging.DEBUG):
    """Initializes logging"""
    global ottd_ctrl_logger, debug, info, warning, error, exception
    fmt = '%(asctime)s %(levelname)s %(name)s %(message)s'
    date_fmt = '%Y-%m-%d_%H:%M:%S'

    logging.basicConfig(filename=None, level=logging.INFO, format=fmt, datefmt=date_fmt)

    ottd_ctrl_logger = logging.getLogger(name)
    ottd_ctrl_logger.setLevel(level)

    debug = ottd_ctrl_logger.debug
    info = ottd_ctrl_logger.info
    warning = ottd_ctrl_logger.warning
    error = ottd_ctrl_logger.error
    exception = ottd_ctrl_logger.exception
