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
import urllib2, urllib

from reporting.exceptions import MessageInvalidError, NetworkConnectionError, RemoteServerError
from reporting.utilities import getLogger

log = getLogger(__name__)

class IOutput(object):
    def push(self, data):
        """
        data is a python object, list or dict
        """
        assert 0, "This method must be defined."
    def close(self):
        pass
        
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
        log.debug("push data to http: %s" % payload[:1024])
        try:
            password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
            password_manager.add_password(None, self.url, self.auth[0], self.auth[1])
            
            auth = urllib2.HTTPBasicAuthHandler(password_manager) # create an authentication handler
            opener = urllib2.build_opener(auth) # create an opener with the authentication handler
            urllib2.install_opener(opener) # install the opener... 
            req = urllib2.Request(self.url, payload, self.headers)
            handler = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            log.error('response code %d' % e.code)
            if e.code == 400 or e.code==500:
                raise MessageInvalidError()
            else:
                raise RemoteServerError()
        except urllib2.URLError as e:
            raise Exception("HTTP error: %s" % e.args)
        else:
            # 200
            response = handler.read()
            log.debug("response %d %s"% (handler.code, response))
            handler.close()

class FileOutput(IOutput):
    def __init__(self, config):
        self.path = config["path"]
        self.__handle=open(self.path, "w")

    def push(self, data):
        if not isinstance(data, list):
            data = [data]
        for line in data:
            self.__handle.write(json.dumps(line) + os.linesep)
        self.__handle.flush()
            
    def close(self):
        log.debug("closing file handle for %s" % self.path)
        if self.__handle:
            self.__handle.close()

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
                try:
                    # if the file has been uploaded and gone, ignore
                    dir_size += os.path.getsize(filename)
                except:
                    pass
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
        json.encoder.FLOAT_REPR = lambda f: ("%.2f" % f)
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