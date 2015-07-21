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
from reporting.utilities import getLogger, excepthook, touch
from reporting.exceptions import MessageInvalidError, NetworkConnectionError, RemoteServerError

log = getLogger(__name__)

class Pusher(multiprocessing.Process):
    """Harvest staged data and push to the API."""
    uuid_pattern = re.compile("^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
    ignore = set()
    max_backoff = 2 * 60

    def __init__(self, output, directory, batch=1, stats_on=False, back_off_indicator=None):
        super(Pusher, self).__init__()
        self.client = output
        self.directory = directory
        self.__running=True
        self.__batch=batch
        self.__back_off=0
        self.__stats_on=stats_on
        self.__back_off_indicator=back_off_indicator

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
                if self.__back_off==0 and self.__back_off_indicator is not None:
                    if os.path.exists(self.__back_off_indicator) and os.path.isfile(self.__back_off_indicator):
                        os.remove(self.__back_off_indicator)
            else:
                num_success=0
                num_invalid=0
                num_error=0
                for (path, dirs, files) in os.walk(self.directory):
                    data_list=[]
                    data_size=0
                    filename_list=[]
                    for i in range(0, len(files)):
                        filename = os.path.join(path, files[i])
                        if not self.uuid_pattern.match(files[i]):
                            continue
                        try:
                            with open(filename, "r") as data:
                                content=data.read()
                                data_size+=len(content)
                                data_list.append(json.loads(content))
                                filename_list.append(filename)
                        except Exception as e:
                            log.exception("unable to read file %s" % filename)
                            pass
                        if data_size>=self.__batch*1024 or i==len(files)-1:
                            try:
                                self.client.push(data_list)
                            except MessageInvalidError as e:
                                self.broken(filename)
                                log.error("error processing %s: %s", filename, str(e))
                                num_invalid+=1
                            except Exception as e:
                                attempt+=1
                                num_error+=1
                                self.__back_off=min(self.max_backoff, attempt + random.random() * pow(2, attempt))
                                if self.__back_off_indicator is not None:
                                    touch(self.__back_off_indicator)
                                log.exception("network or remote server error, back off for %d seconds" % self.__back_off)
                            if self.__back_off==0:
                                attempt=0
                                data_size=0
                                num_success+=len(data_list)
                                del data_list[:]
                                for file_name in filename_list:
                                    os.remove(file_name)
                                del filename_list[:]
                            else:
                                break
                        if not self.__running:
                            break
                    if self.__back_off>0:
                        break
                num_total=num_success+num_invalid+num_error
                if num_total>0 and self.__stats_on==True:
                    log.info("Messages total: %d; success: %d; invalid: %d; error: %d" % (num_total,num_success,num_invalid,num_error) )
                time.sleep(1)
        log.info("Pusher has stopped at %s" % datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y"))
        