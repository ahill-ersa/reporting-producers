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
import threading

import requests
from requests.exceptions import ConnectionError
from reporting.exceptions import MessageInvalidError, NetworkConnectionError, RemoteServerError
from reporting.utilities import getLogger

log = getLogger(__name__)

class IOutput(object):
    def push(self, data):
        """
        data is a python object, list or dict
        """
        assert 0, "This method must be defined."
        
class KafkaHTTPOutput(IOutput):
    """Reporting API client."""
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    def __init__(self, config):
        self.url = config["url"]
        self.auth = (config["username"], config["token"])
        self.attempts = config.get("attempts", 3)
        self.verify = config.get("verify", True)

    def push(self, data):
        if not isinstance(data, list):
            data = [data]
        payload = json.dumps(data)
        log.debug("push data to http: %s" % payload)
        try:
            response = requests.post(self.url, headers=self.headers, auth=self.auth, data=payload, verify=self.verify)
        except ConnectionError:
            raise NetworkConnectionError()
        log.debug("response %s"%response)
        if response.status_code == 204:
            return
        elif response.status_code == 400:
            raise MessageInvalidError()
        elif response.status_code == 500:
            raise RemoteServerError()
        else:
            raise Exception("HTTP error: %i %s" % (response.status_code, response.text))

class CheckDir(object):
    """Ensure sufficient capacity for staging data."""

    def __init__(self, directory = ".", cache_size=100, check_period=30):
        self.__directory = directory
        self.__cache_size = cache_size
        self.__check_period = check_period
        self.__last_check = 0
        self.__ok = False

    def perform_check(self):
        actual_size=self.get_directory_size(self.__directory)
        log.debug("size of dir %s is %d, cache size is %d"%(self.__directory, actual_size, self.__cache_size))
        return self.__cache_size > actual_size

    def is_ok(self):
        if (time.time() - self.__last_check) >= self.__check_period:
            self.__ok = self.perform_check()
        return self.__ok
    
    def get_directory_size(self, directory):
        dir_size = 0
        for (path, dirs, files) in os.walk(directory):
            for file in files:
                filename = os.path.join(path, file)
                dir_size += os.path.getsize(filename)
        return dir_size

class BufferOutput(IOutput):
    """Stage data prior to upload."""
    def __init__(self, config):
        self.directory = config['directory']
        self.check_dir = CheckDir(config['directory'], config['size'])
        self.log_space_warning=False
        self.queue=[]
        self.write_lock = threading.Lock()

    def push(self, data):
        with self.write_lock:
            self.queue.append(data)
        return True
    
    def execute(self):
        if len(self.queue)>0:
            with self.write_lock:
                data = self.queue.pop()
            if len(data) == 0:
                return
            if self.check_dir.is_ok():
                self.log_space_warning=False
                log.debug("data to save: %s"%data)
                data_id = data["id"]
                filename = "%s/%s" % (self.directory, data_id)
                filename_tmp = "%s/.%s" % (self.directory, data_id)
                try:
                    with open(filename_tmp, "w") as output:
                        output.write(json.dumps(data))
                    os.rename(filename_tmp, filename)
                except Exception as e:
                    log.error("unexpected error: %s", str(e))
                    return
            else:
                if not self.log_space_warning:
                    log.warn("Cache directory %s has reached its capacity.", self.directory)
                self.log_space_warning=True
                
    def cleanup(self):
        log.debug("write all data to cache before exit...")
        while len(self.queue)>0:
            self.execute()