#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, get_hostname
import json
import time

log = getLogger(__name__)

def value(s):
    if s.isdigit():
        return int(s)
    numeric = float(s[:-1])
    if s.endswith("K"):
        return numeric
    elif s.endswith("M"):
        return numeric * 1024
    elif s.endswith("G"):
        return numeric * 1024 * 1024
    elif s.endswith("T"):
        return numeric * 1024 * 1024 *1024

class KstatInput(IDataSource):
    def get_data(self, **kwargs):
        dir = "/proc/spl/kstat/zfs/"
        files = [ "arcstats", "dmu_tx", "zfetchstats", "zil" ]
        data={}
        for file in files:
            data[file] = {}
            linenum = 0
            log.debug("reading file %s"% (dir + file))
            for line in open(dir + file, "r"):
                linenum += 1
                if linenum > 2:
                    line = line.split()
                    data[file][line[0]] = int(line[2])
        
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data

class IostatParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        data={}
        for line in lines[3:]:
            line = line.split()
            log.debug("iostat %s"%line)
            data[line[0]]={}
            data[line[0]]["alloc"] = value(line[1])
            data[line[0]]["free"] = value(line[2])
            data[line[0]]["kb_read"] = value(line[5])
            data[line[0]]["kb_write"] = value(line[6])
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data


class ListParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        data={}
        for line in lines[1:]:
            line = line.split()
            data[line[0]]={}
            data[line[0]]["available"] = value(line[1])
            data[line[0]]["used"] = value(line[2])
            data[line[0]]["ratio"] = line[3]
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data

    