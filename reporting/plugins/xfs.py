#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, list_to_dict, get_hostname
import json
import time

log = getLogger(__name__)

class QuotaReportParser(IParser):
    def __init__(self, exclude_users):
        self.__exclude_users=exclude_users
    def parse(self, data):
        result = {}
        
        result["timestamp"] = int(time.time())
        result["hostname"] = get_hostname()
        result["filesystems"] = []
        
        for line in data.split("\n"):
            line = line.strip()
            tokens = line.split()
        
            if line.startswith("User quota on"):
                filesystem = {
                    "device" : tokens[4][1:-1],
                    "filesystem" : tokens[3],
                    "quota" : []
                }
                result["filesystems"].append(filesystem)
                continue
        
            if line.startswith("User ID") or line.startswith("-") or line.startswith("Blocks") or (len(line) == 0):
                continue
        
            entry = {}
            entry["username"] = tokens[0]
            if entry["username"] in self.__exclude_users:
                continue
            entry["used"] = int(tokens[1])
            entry["soft"] = int(tokens[2])
            entry["hard"] = int(tokens[3])
            filesystem["quota"].append(entry)
        
        return result
