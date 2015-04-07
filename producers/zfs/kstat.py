#!/usr/bin/env python

import os, platform, subprocess, sys, json, uuid, time

host = platform.node()

data = { "schema" : "zfs.kstat", "version" : 1, "host" : host, "timestamp" : int(time.time()), "id" : str(uuid.uuid4()) }

dir = "/proc/spl/kstat/zfs/"
files = [ "arcstats", "dmu_tx", "zfetchstats", "zil" ]

for file in files:
    data[file] = {}
    linenum = 0
    for line in open(dir + file, "r"):
        linenum += 1
        if linenum > 2:
            line = line.split()
            data[file][line[0]] = int(line[2])

print json.dumps(data)
