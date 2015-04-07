#!/usr/bin/env python

import json
import os
import platform
import sys
import time
import uuid

exclude_users = [ "root", "bin", "daemon", "games", "gdm", "rpcuser", "nagios", "apache", "nobody" ]

data = {}

data["id"] = str(uuid.uuid4())
data["timestamp"] = int(time.time())
data["hostname"] = platform.node()
data["schema"] = "xfs_quota"
data["version"] = 1
data["filesystems"] = []

for line in sys.stdin:
    line = line.strip()
    tokens = line.split()

    if line.startswith("User quota on"):
        filesystem = {
            "device" : tokens[4][1:-1],
            "filesystem" : tokens[3],
            "quota" : []
        }
        data["filesystems"].append(filesystem)
        continue

    if line.startswith("User ID") or line.startswith("-") or line.startswith("Blocks") or (len(line) == 0):
        continue

    entry = {}
    entry["username"] = tokens[0]
    if entry["username"] in exclude_users:
        continue
    entry["used"] = int(tokens[1])
    entry["soft"] = int(tokens[2])
    entry["hard"] = int(tokens[3])
    filesystem["quota"].append(entry)

print json.dumps(data)
