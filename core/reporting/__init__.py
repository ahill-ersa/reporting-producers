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
import yaml


log_handler = logging.StreamHandler()
log_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))


def prettyprint(x):
    print json.dumps(x, indent=4, sort_keys=True)


class Reporting(object):
    """Reporting API client."""
    log = logging.getLogger("reporting-client")
    log.addHandler(log_handler)

    max_backoff = 60 * 60

    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    def __init__(self, config, log_level=logging.WARNING):
        self.base = "https://%s/v1/" % config["server"]
        self.auth = (config["username"], config["token"])
        self.attempts = config.get("attempts", 180)
        self.verify = config.get("verify", True)
        self.log.setLevel(log_level)

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
            print payload
            response = requests.post(self.url("topic"), headers=self.headers, auth=self.auth, data=json.dumps(data), verify=self.verify)
            if response.status_code == 204:
                return
            elif response.status_code == 500:
                self.log.warning("server error: backing off and retrying")
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


class Buffer(object):
    """Stage data prior to upload."""
    log = logging.getLogger("reporting-buffer")
    log.addHandler(log_handler)

    def __init__(self, directory=".", log_level=logging.WARNING):
        self.directory = directory
        self.check_dir = CheckDir(directory)
        self.log.setLevel(log_level)

    def execute(self):
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
                    self.log.error("unexpected error: %s", str(e))
            else:
                self.log.error("insufficient free space: %s", self.directory)


class Pusher(object):
    """Harvest staged data and push to the API."""
    uuid_pattern = re.compile("^[0-9a-fA-F]{8}-([0-9a-fA-F]{4}-){3}[0-9a-fA-F]{12}$")
    ignore = set()

    log = logging.getLogger("reporting-pusher")
    log.addHandler(log_handler)

    def __init__(self, client, directory=".", sleep=2, log_level=logging.WARNING):
        self.client = client
        self.sleep = sleep
        self.directory = directory
        self.log.setLevel(log_level)

    def broken(self, filename):
        if filename not in self.ignore:
            try:
                os.rename(filename, filename + ".broken")
            except Exception as e:
                self.ignore.add(filename)
                self.log.warning("couldn't rename file %s: %s", filename, str(e))

    def execute(self):
        while True:
            for filename in [name for name in os.listdir(self.directory) if self.uuid_pattern.match(name)]:
                filename = "%s/%s" % (self.directory, filename)
                try:
                    with open(filename, "r") as data:
                        self.client.push(json.loads(data.read()))
                    os.remove(filename)
                except Exception as e:
                    self.broken(filename)
                    self.log.error("error processing %s: %s", filename, str(e))
            time.sleep(self.sleep)
