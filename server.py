# -*- coding: utf-8 -*-

"""
Contains commands
"""

# standard
from contextlib import contextmanager
import logging
import signal
import time

# related
import sh

# project
import log


class OpenTTDServer:
    def __init__(self,
                 out_log='openttd_server.out',
                 err_log='openttd_server.err',
                 startup_time_s=2):
        """
        :param out_log: stdout redirection
        :param err_log: stderr redirection
        :param startup_time_s: Wait time after starting and stopping server
        """
        # stdout and stderr redirection
        self.out_log = out_log
        self.err_log = err_log
        # We sleep this amount of seconds after starting and stopping the server
        self.start_stop_time_s = startup_time_s
        # True if the server has been started (and not stopped)
        self.running = False
        # sh.RunningCommand once the server is started
        self.process = None
        # True when we intentionally try to stop the server
        self.stopping = False
        # Our logger
        self.log = logging.getLogger('OpenTTDServer')

    @contextmanager
    def started(self):
        """
        Use this to do things while server is running
        and stop it once done
        """
        self.start()
        try:
            yield self
        finally:
            self.stop()

    def start(self):
        """Starts the OpenTTD server"""
        assert self.running is False, "Server already running"
        self.running = True
        self.log.info("Starting")
        try:
            self.process = sh.openttd('-D',
                                      _out='openttd_server.out',
                                      _err='openttd_server.err',
                                      _bg=True,
                                      _done=self._server_stopped)
        except Exception:
            # TODO be more specific
            log.exception("Error while starting OpenTTD server")
            self.running = False
        time.sleep(self.start_stop_time_s)
        if not self.running:
            raise Exception("Server failed starting")
        self.log.info("Started")

    def stop(self):
        """Stops the server with a SIGINT"""
        if self.running:
            self.log.debug("Stopping server with SIGINT")
            self.stopping = True
            self.process.signal(signal.SIGINT)
            time.sleep(self.start_stop_time_s)

    def _server_stopped(self, *args, **kwargs):
        """Called when server stops"""
        if self.stopping:
            self.log.info("Stopped")
        else:
            self.log.error("Stopped")
            # TODO some better message
        self.stopping = False
        self.running = False
        self.process = None
