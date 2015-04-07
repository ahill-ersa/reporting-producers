#!/usr/bin/python

import os, platform, subprocess, sys, json, time, uuid

interface = "bond0"
data = { "schema" : "ifstat", "version" : 1, "interface" : interface, "hostname" : platform.node() }

cmd = [ "ifstat", "-i", interface, "-n", "5" ]

proc = subprocess.Popen(cmd, stdout = subprocess.PIPE)

while True:
    line = proc.stdout.readline().rstrip()
    if ("KB" in line) or ("bond" in line):
        continue

    line = line.split()
    data["id"] = str(uuid.uuid4())
    data["time"] = int(time.time())
    data["kb_in"] = float(line[0])
    data["kb_out"] = float(line[1])
    print json.dumps(data)
