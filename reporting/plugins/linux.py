#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
import re
from fnmatch import fnmatch
from reporting.utilities import getLogger, get_hostname, init_message
import time
import json, grp, os, pwd, stat, sys
from os.path import join

log = getLogger(__name__)

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
        output = {}
        output['df'] = result
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output
    
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
        output = {}
        output['ifstat'] = data
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output

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
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data

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
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data

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
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data

class FileSystemUsage(IDataSource):
    def __init__(self, path):
        self.__path=path
    def get_data(self, **kwargs):
        inodes = set()
        users = {}
        groups = {}
        data = init_message()
         
        data["fs"] = { "name" : self.__path }
        fs_raw = str(os.statvfs(self.__path))
        for kv in [field.split("=") for field in fs_raw[fs_raw.index("(")+1:-1].split(", ")]:
            data["fs"][kv[0][2:]] = int(kv[1])
         
        data["usage"] = {}
        for root, dirs, files in os.walk(self.__path):
            for name in files:
                filename = join(root, name)
                metadata = os.lstat(filename)
                if stat.S_ISREG(metadata.st_mode):
                    if metadata.st_nlink == 1 or metadata.st_ino not in inodes:
                        if metadata.st_uid not in users:
                            try:
                                users[metadata.st_uid] = pwd.getpwuid(metadata.st_uid).pw_name
                            except:
                                users[metadata.st_uid] = metadata.st_uid
                        if metadata.st_gid not in groups:
                            try:
                                groups[metadata.st_gid] = grp.getgrgid(metadata.st_gid).gr_name
                            except:
                                groups[metadata.st_gid] = metadata.st_gid
                     
                        user = users[metadata.st_uid]
                        group = groups[metadata.st_gid]
                        key = str(user) + "/" + str(group)
                     
                        if key not in data["usage"]:
                            data["usage"][key] = { "files" : 0, "blocks" : 0, "bytes" : 0 }
                     
                        data["usage"][key]["files"] += 1
                        data["usage"][key]["bytes"] += metadata.st_size
                        data["usage"][key]["blocks"] += metadata.st_blocks
                    if metadata.st_nlink > 1:
                        inodes.add(metadata.st_ino)
         
        return data     
     
