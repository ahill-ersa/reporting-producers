#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
import re
from fnmatch import fnmatch
from reporting.utilities import getLogger, get_hostname
import time

log = getLogger(__name__)

class ProcParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        result=[]
        for line in lines[3:-2]:
            items = [item.strip() for item in line.split('|')]
            #print items
            process = {}
            process["id"] = items[1]
            process["user"] = items[2]
            if len(items[3])>0:
                process["host"] = items[3]
            if len(items[4])>0:
                process["db"] = items[4]
            process["command"] = items[5]
            process["time"] = int(items[6])
            if len(items[7])>0:
                process["state"] = items[7]
            if len(items[8])>0:
                process["info"] = items[8]
            result.append(process)
        output = {}
        output['processes'] = result
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output
    
class StatusParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        output = {}
        for line in lines[3:-2]:
            items = [item.strip() for item in line.split('|')]
            output[items[1]]=items[2]
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output
