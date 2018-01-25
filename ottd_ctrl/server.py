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


class OpenTTDServer:
    def __init__(self,
                 out_log='openttd_server.out',
                 err_log='openttd_server.err',
                 start_stop_time=2,
                 config_file=None):
        """
        :param out_log: stdout redirection
        :param err_log: stderr redirection
        :param start_stop_time: Wait time after starting and stopping server
        """
        # stdout and stderr redirection
        self.out_log = out_log
        self.err_log = err_log
        # configuration file
        self._config_file = config_file
        # We sleep this amount of seconds after starting and stopping the server
        self.start_stop_time_s = start_stop_time
        # True if the server has been started (and not stopped)
        self.running = False
        # sh.RunningCommand once the server is started
        self.process = None
        # True when we intentionally try to stop the server
        self._stopping = False
        # Our logger
        self.log = logging.getLogger('OpenTTDServer')

    @contextmanager
    def stopping(self):
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

        args = ['-D']  # dedicated server
        if self._config_file is not None:
            args.extend(['-c', self._config_file])
        try:
            self.process = sh.openttd(*args,
                                      _out='openttd_server.out',
                                      _err='openttd_server.err',
                                      _bg=True,
                                      _done=self._server_stopped)
        except Exception:
            # TODO be more specific
            self.log.exception("Error while starting OpenTTD server")
            self.running = False
        time.sleep(self.start_stop_time_s)
        if not self.running:
            raise Exception("Server failed starting")
        self.log.info("Started")

    def stop(self):
        """Stops the server with a SIGINT"""
        if self.running:
            self.log.debug("Stopping server with SIGINT")
            self._stopping = True
            self.process.signal(signal.SIGINT)
            time.sleep(self.start_stop_time_s)

    def _server_stopped(self, command, success, exit_code):
        """Called when server stops (in another thread)"""
        if exit_code < 0:
            self.log.error('Terminated by signal %s', exit_code)
        elif exit_code > 0:
            self.log.error('Terminated with exit code %s', exit_code)
        if self._stopping:
            # we are stopping the server, that's OK
            self.log.info("Stopped")
        else:
            self.log.error("Unexpectedly stopped")
            # TODO some better message
        self._stopping = False
        self.running = False
        self.process = None
