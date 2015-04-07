#!/usr/bin/env python

import os, platform, subprocess, sys, json, uuid, time

host = platform.node()
pool = "instances"

cmd = [ "zpool", "iostat", pool, "5" ]

data = { "schema" : "zfs.iostat", "version" : 1, "pool" : pool, "host" : host }

proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

def value(s):
    if s == "0":
        return 0
    numeric = float(s[:-1])
    if s.endswith("K"):
        return numeric
    elif s.endswith("M"):
        return numeric * 1024
    elif s.endswith("G"):
        return numeric * 1024 * 1024

while True:
    line = proc.stdout.readline().rstrip()
    if ("instances" not in line):
        continue

    data["timestamp"] = int(time.time())
    data["id"] = str(uuid.uuid4())
    line = line.split()
    data["kb_read"] = value(line[5])
    data["kb_write"] = value(line[6])
    print json.dumps(data)
