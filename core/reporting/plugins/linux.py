#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
import re
from fnmatch import fnmatch

class DfParser(IParser):
    def __init__(self, exclude_devices):
        self.__exclude_devices=exclude_devices
    def parse(self, data):
        lines=data.split('\n')
        result=[]
        for line in lines:
            if line.startswith("Filesystem "):
                continue
            line = line.strip().split()
            filesystem = {}
            filesystem["device"] = line[0]
            if filesystem["device"] in self.__exclude_devices:
                continue
            filesystem["size"] = int(line[1])
            filesystem["used"] = int(line[2])
            filesystem["available"] = int(line[3])
            filesystem["mountpoint"] = line[5]
            result.append(filesystem)
        return str(result).replace("'",'"')
    
class IfstatParser(IParser):
    def __init__(self, device):
        self.__device=device
    def parse(self, data):
        lines=data.split('\n')
        data=[]
        for line in lines[2:]:
            line = line.split()
            data["kb_in"] = float(line[0])
            data["kb_out"] = float(line[1])
        return str(data).replace("'",'"')

class CPUParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        data={}
        for line in lines:
            if line.startswith('cpu'):
                line = line.split()
                data[line[0]] = {}
                data[line[0]]['user'] = int(line[1])
                data[line[0]]['nice'] = int(line[2])
                data[line[0]]['system'] = int(line[3])
                data[line[0]]['idle'] = int(line[4])
                if len(line)>=8:
                    data[line[0]]['wait'] = int(line[5])
                    data[line[0]]['interrupt'] = int(line[6])
                    data[line[0]]['softirq'] = int(line[7])
                    if len(line)>=9:
                        data[line[0]]['steal'] = int(line[8])
        return str(data).replace("'",'"')

class MemParser(IParser):
    def parse(self, data):
        lines=data.split('\n')
        data={}
        for line in lines:
            line = line.split()
            if line[0].startswith('MemTotal'):
                data['total'] = int(line[1])
            if line[0].startswith('MemFree'):
                data['free'] = int(line[1])
            if line[0].startswith('Buffers'):
                data['buffered'] = int(line[1])
            if line[0].startswith('Cached'):
                data['cached'] = int(line[1])
            if line[0].startswith('Slab'):
                data['slab_total'] = int(line[1])
            if line[0].startswith('SReclaimable'):
                data['slab_reclaimable'] = int(line[1])
            if line[0].startswith('SUnreclaim'):
                data['slab_unreclaimable'] = int(line[1])
        data['used'] = data['total'] - (data['free'] + data['buffered'] + data['cached'] + data['slab_total'])
        return str(data).replace("'",'"')

class NetDevParser(IParser):
    fields = {
        "bytes" : 0,
        "packets" : 1,
        "errors" : 2,
        "dropped" : 3
    }
    
    directions = {
        "rx" : 2,
        "tx" : 10
    }
    def __init__(self, include_devices):
        self.__include_devices=include_devices
    def parse(self, data):
        pattern = re.compile("[ :]+")
        lines=data.split('\n')
        data={}
        for line in lines:
            if ":" in line:
                line = pattern.split(line)
                interface = line[1]
                included=False
                for dev in self.__include_devices:
                    if fnmatch(interface, dev):
                        included=True
                        break
                if not included:
                    continue
                data[interface] = {}
                for direction in self.directions:
                    data[interface][direction] = {}
                    for field in self.fields:
                        data[interface][direction][field] = int(line[self.directions[direction] + self.fields[field]])
        return str(data).replace("'",'"')
