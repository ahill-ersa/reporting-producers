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

hostname = platform.node()
session = str(uuid.uuid4())

for line in sys.stdin:
    line = line.strip()

    data = {}

    data["id"] = str(uuid.uuid4())
    data["session"] = session
    data["hostname"] = hostname
    data["schema"] = "pbs.log"
    data["version"] = 1

    data["pbs"] = {}

    tokens = [x.lower() for x in line.split(";")]

    data["timestamp"] = int(time.mktime(time.strptime(tokens[0], "%m/%d/%Y %H:%M:%S")))

    job_states = {
        "job deleted" : "deleted",
        "job run" : "run",
        "dequeuing" : "dequeued",
        "job queued" : "queued",
        "exit_status" : "exited"
    }

    event_type = tokens[3]
    event_id = tokens[4]
    event_description = tokens[5]

    if event_type == "svr":
        if "job nanny" in event_description:
            # example
            # 08/06/2014 01:03:59;0001;PBS_Server;Svr;PBS_Server;LOG_ERROR::job nanny, exiting job '786299.tizard1' still exists, sending a SIGKILL
            data["pbs"]["job"] = event_description.split("'")[1]
            data["pbs"]["state"] = event_description.split()[-1]
    elif event_type == "job":
        for state in job_states:
            if state in event_description:
                data["pbs"]["job"] = event_id
                data["pbs"]["state"] = job_states[state]
                break

    if "job" not in data["pbs"]:
        continue
    else:
        if data["pbs"]["state"] == "exited":
            # example (split)
            # 08/06/2014 00:29:47;0010;PBS_Server;Job;796694.tizard1;Exit_status=0 resources_used.cput=18:25:07
            # resources_used.mem=2569184kb resources_used.vmem=14061332kb resources_used.walltime=02:59:47
            data["pbs"]["stats"] = {}
            stats = event_description.split()
            for stat in stats:
                stat = stat.split("=")

                if "." in stat[0]:
                    stat[0] = stat[0].split(".")
                if reduce(lambda x, y: x and y, [str.isdigit(_) for _ in stat[1]]):
                    stat[1] = int(stat[1])

                if isinstance(stat[0], str):
                    data["pbs"]["stats"][stat[0]] = stat[1]
                elif isinstance(stat[0], list):
                    list_to_dict(data["pbs"]["stats"], stat[0], stat[1])
        elif data["pbs"]["state"] == "queued":
            # example (split)
            # 08/06/2014 00:44:15;0008;PBS_Server;Job;796871.tizard1;Job Queued at request of foo@tizard1,
            # owner = foo@tizard1, job name = something.sh, queue = gtx
            data["pbs"]["attributes"] = {}
            for kv in event_description.split(",")[1:]:
                kv = kv.split("=")
                kv = [_.strip() for _ in kv]
                data["pbs"]["attributes"][kv[0].replace(" ", "_")] = kv[1]
                if "owner" in data["pbs"]["attributes"]:
                    data["pbs"]["attributes"]["owner"] = data["pbs"]["attributes"]["owner"].split("@")[0]

        print json.dumps(data)
