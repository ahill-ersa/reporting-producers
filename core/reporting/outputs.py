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

import requests
from reporting.utilities import getLogger

log = getLogger(__name__)

class IOutput(object):
    def push(self, data):
        assert 0, "This method must be defined."
        
class HTTPOutput(IOutput):
    """Reporting API client."""
    max_backoff = 60 * 60

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    def __init__(self, config):
        self.base = "https://%s/v1/" % config["server"]
        self.auth = (config["username"], config["token"])
        self.attempts = config.get("attempts", 180)
        self.verify = config.get("verify", True)

    def url(self, obj, key=None):
        url_str = "%s%s/" % (self.base, obj)
        if key:
            return "%s%s" % (url_str, key)
        else:
            return url_str

    def backoff(self, attempt):
        time.sleep(min(self.max_backoff, attempt + random.random() * pow(2, attempt)))

    def list(self, obj):
        response = requests.get(self.url(obj), headers=self.headers, auth=self.auth)
        if response.status_code == 200:
            return response
        else:
            raise Exception("HTTP error: %i %s" % (response.status_code, response.text))

    def push(self, data):
        if not isinstance(data, list):
            data = [data]
        attempt = 0
        while attempt < self.attempts:
            payload = json.dumps(data)
            log.debug("push data to http: %s" % payload)
            response = requests.post(self.url("topic"), headers=self.headers, auth=self.auth, data=json.dumps(data), verify=self.verify)
            if response.status_code == 204:
                return
            elif response.status_code == 500:
                log.warning("server error: backing off and retrying")
                self.backoff(attempt)
            else:
                raise Exception("HTTP error: %i %s" % (response.status_code, response.text))
            attempt += 1
        raise Exception("Message delivery failure: exhausted %i attempts." % self.attempts)

class CheckDir(object):
    """Ensure sufficient capacity for staging data."""
    last_check = 0
    ok = False

    def __init__(self, directory = ".", min_free_mb=100, check_period=30):
        self.directory = directory
        self.min_free_mb = min_free_mb
        self.check_period = check_period
        self.last_check = 0

    def perform_check(self):
        self.last_check = time.time()
        filesystem = os.statvfs(self.directory)
        free = (filesystem.f_bavail * filesystem.f_frsize) / (1024 * 1024)
        return free >= self.min_free_mb

    def is_ok(self):
        if (time.time() - self.last_check) >= self.check_period:
            self.ok = self.perform_check()
        return self.ok

class BufferOutput(IOutput):
    """Stage data prior to upload."""
    def __init__(self, config):
        self.directory = config['directory']
        self.check_dir = CheckDir(config['directory'])

    def push(self, data):
        return
    
    def execute(self):
        log_space_warning=False
        while True:
            data = sys.stdin.readline().strip()
            if len(data) == 0:
                break
            if self.check_dir.is_ok():
                data_id = json.loads(data)["id"]
                filename = "%s/%s" % (self.directory, data_id)
                filename_tmp = "%s/.%s" % (self.directory, data_id)
                try:
                    with open(filename_tmp, "w") as output:
                        output.write(data)
                    os.rename(filename_tmp, filename)
                except Exception as e:
                    log.error("unexpected error: %s", str(e))
            else:
                if not log_space_warning:
                    log.warn("Cache directory %s has reached its capacity.", self.directory)
                log_space_warning=True
