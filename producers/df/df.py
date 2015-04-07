#!/usr/bin/env python

import json
import os
import platform
import sys
import time
import uuid

exclude_devices = [ "tmpfs" ]

data = {}

data["id"] = str(uuid.uuid4())
data["timestamp"] = int(time.time())
data["hostname"] = platform.node()
data["schema"] = "df"
data["version"] = 1
data["filesystems"] = []

for line in sys.stdin:
    if line.startswith("Filesystem "):
        continue
    line = line.strip().split()
    filesystem = {}
    filesystem["device"] = line[0]
    if filesystem["device"] in exclude_devices:
        continue
    filesystem["size"] = int(line[1])
    filesystem["used"] = int(line[2])
    filesystem["available"] = int(line[3])
    filesystem["mountpoint"] = line[5]
    data["filesystems"].append(filesystem)

print json.dumps(data)
