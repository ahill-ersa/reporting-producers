#!/usr/bin/env python

import os, platform, subprocess, sys, json, uuid, time

host = platform.node()

data = { "schema" : "zfs.list", "version" : 1, "host" : host, "timestamp" : int(time.time()), "id" : str(uuid.uuid4()) }

numbers = [ "used", "available" ]
ratio = [ "compressratio" ]

for line in sys.stdin:
    line = line.split()
    if not "fs" in data:
        data["fs"] = line[0]
    field = line[1]
    value = line[2]
    if field in numbers:
        data[field] = int(value)
    elif field in ratio:
        data[field] = float(value[:-1])
    else:
        data[field] = value
