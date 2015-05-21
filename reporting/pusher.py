#!/usr/bin/env python

# pylint: disable=broad-except

import json
import logging
import os
import random
import re
import sys
import time
import traceback
import uuid
import multiprocessing
import datetime
import signal

import yaml
from reporting.utilities import getLogger, excepthook
from reporting.exceptions import MessageInvalidError, NetworkConnectionError, RemoteServerError

log = getLogger(__name__)

class Pusher(multiprocessing.Process):
    """Harvest staged data and push to the API."""
    uuid_pattern = re.compile("^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
    ignore = set()
    max_backoff = 2 * 60

    def __init__(self, output, directory, batch=1):
        super(Pusher, self).__init__()
        self.client = output
        self.directory = directory
        self.__running=True
        self.__batch=batch
        self.__back_off=0

    def __sigTERMhandler(self, signum, frame):
        log.debug("Caught signal %d. Exiting" % signum)
        self.quit()
        
    def quit(self):
        self.__running=False

    def broken(self, filename):
        if filename not in self.ignore:
            try:
                os.rename(filename, filename + ".broken")
            except Exception as e:
                self.ignore.add(filename)
                log.warning("couldn't rename file %s: %s", filename, str(e))

    def backoff(self, attempt):
        time.sleep(min(self.max_backoff, attempt + random.random() * pow(2, attempt)))

    def run(self):
        # Install signal handlers
        signal.signal(signal.SIGTERM, self.__sigTERMhandler)
        signal.signal(signal.SIGINT, self.__sigTERMhandler)
        # Ensure unhandled exceptions are logged
        sys.excepthook = excepthook
        log.info("Pusher has started at %s" % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        attempt=0
        while self.__running:
            if self.__back_off>0:
                time.sleep(1)
                self.__back_off-=1
            #log.debug("getting files to push...")
            for filename in [name for name in os.listdir(self.directory) if self.uuid_pattern.match(name)]:
                filename = "%s/%s" % (self.directory, filename)
                try:
                    with open(filename, "r") as data:
                        self.client.push(json.loads(data.read()))
                    os.remove(filename)
                    attempt=0
                except MessageInvalidError as e:
                    self.broken(filename)
                    log.error("error processing %s: %s", filename, str(e))
                except Exception as e:
                    attempt+=1
                    self.__back_off=min(self.max_backoff, attempt + random.random() * pow(2, attempt))
                    log.error("network or remote server error, back off for %d seconds" % self.__back_off)
                    break
            time.sleep(1)
        log.info("Pusher has stopped at %s" % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
