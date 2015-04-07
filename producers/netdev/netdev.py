#!/usr/bin/env python

import json
import os
import platform
import re
import sys
import time
import uuid

pattern = re.compile("[ :]+")

data = {}

data["id"] = str(uuid.uuid4())
data["timestamp"] = int(time.time())
data["hostname"] = platform.node()
data["schema"] = "netdev"
data["version"] = 1
data["netdev"] = {}

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

for line in sys.stdin:
    if ":" in line:
        line = pattern.split(line)
        interface = line[1]
        data["netdev"][interface] = {}
        for direction in directions:
            data["netdev"][interface][direction] = {}
            for field in fields:
                data["netdev"][interface][direction][field] = int(line[directions[direction] + fields[field]])

print json.dumps(data)
