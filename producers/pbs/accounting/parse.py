#!/usr/bin/env python

import json
import os
import platform
import sys
import time
import uuid

def list_to_dict(d, l, value):
    if len(l) == 1:
        d[l[0]] = value
    else:
        if l[0] not in d:
            d[l[0]] = {}
        list_to_dict(d[l[0]], l[1:], value)

# example (split)
# 07/11/2013 23:29:26;S;169651.tizard1;user=blah group=physics jobname=stuff queue=tizard
# ctime=1373516906 qtime=1373516906 etime=1373516906 start=1373551166 owner=blah@tizard1
# exec_host=tizard09/47+tizard09/46 ... tizard07/0 Resource_List.mem=32gb Resource_List.neednodes=2:ppn=32 Resource_List.nodect=2
# Resource_List.nodes=2:ppn=32 Resource_List.vmem=32gb Resource_List.walltime=72:00:00

hostname = platform.node()
session = str(uuid.uuid4())

output = []

for line in sys.stdin:
    line = line.strip()

    data = {}

    data["id"] = str(uuid.uuid4())
    data["session"] = session
    data["hostname"] = hostname
    data["schema"] = "pbs.accounting"
    data["version"] = 1

    data["pbs"] = {}

    tokens = [x.lower() for x in line.split(";")]

    data["timestamp"] = int(time.mktime(time.strptime(tokens[0], "%m/%d/%Y %H:%M:%S")))

    job_states = {
        "s" : "run",
        "q" : "queued",
        "e" : "exited",
        "d" : "deleted"
    }

    for state in job_states:
        if state == tokens[1]:
            data["pbs"]["state"] = job_states[state]
            break

    data["pbs"]["job"] = tokens[2]
    data["pbs"]["attributes"] = {}

    for attr in tokens[3].split():
        kv = attr.split("=")
        if reduce(lambda x, y: x and y, [str.isdigit(_) for _ in kv[1]]):
            kv[1] = int(kv[1])
        elif kv[0] == "exec_host":
            hosts = {}
            for slot in kv[1].split("+"):
                slot = slot.split("/")
                slot[1] = int(slot[1])
                if slot[0] not in hosts:
                    hosts[slot[0]] = [ slot[1] ]
                else:
                    hosts[slot[0]].append(slot[1])
            kv[1] = hosts
        elif kv[0] == "owner":
            kv[1] = kv[1].split("@")[0]

        if "." in kv[0]:
            kv[0] = kv[0].split(".")

        if isinstance(kv[0], str):
            data["pbs"]["attributes"][kv[0]] = kv[1]
        elif isinstance(kv[0], list):
            list_to_dict(data["pbs"]["attributes"], kv[0], kv[1])

    output.append(data)

print json.dumps(output)
