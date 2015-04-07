#!/usr/bin/env python

import os, time, json, platform, uuid

data = { "schema" : "loadavg", "version" : 1, "host" : platform.node(), "time" : int(time.time()), "id" : str(uuid.uuid4()) }

while True:
    data["id"] = str(uuid.uuid4())
    data["time"] = int(time.time())
    with open("/proc/loadavg", "r") as loadavg:
        line = loadavg.read().split()
        data["1min"] = float(line[0])
        data["5min"] = float(line[1])
        data["15min"] = float(line[2])

    print json.dumps(data)

    time.sleep(30)
