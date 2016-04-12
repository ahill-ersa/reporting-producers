"""
Parse raw pbs accounting logs and save the result into a JSON file.
This JSON file can be ingested through reporting API server.
"""

import sys
sys.path.insert(1, "..")


import os
import glob
import json
import uuid
from argparse import ArgumentParser

from reporting.plugins.pbs import AccountingLogParser

# Information used when packaging parsed log into a Reporting Producer's message
config = {"metadata": { "schema": "pbs.accounting.log", "version": 1}}

# Below functions are modifed based on the functions in reporting package
def query_files(path):
    file_list = []
    for file_path in glob.glob(path):
        file_list.append(file_path)
    file_list.sort()
    return file_list

def generate_payload(data):
    payload = {"id": str(uuid.uuid4()),
               "session": str(uuid.uuid4()),
               "data": data
              }
    if 'metadata' in config:
        for m in config['metadata']:
            payload[m] = config['metadata'][m]
    return payload

parser = ArgumentParser(description="Parse pbs.accounting.log to generate Producer's messagess")
parser.add_argument('path', default='pbs_accounting_log',
    help='Path to the logs to be processed. Default = pbs_accounting_log')

args = parser.parse_args()

# Check that the configuration file exists
if not os.path.exists(args.path):
    print("Patch %s cannot be found" % args.path)
    exit(1)

args.path = os.path.normpath(args.path)
print("Will process logs using pbs.account.log parser - AccountingLogParser from %s" % args.path)

log_source = os.path.basename(args.path)

results = []
alog = AccountingLogParser()
logs = query_files(args.path + "/*");
for log in logs:
    print(log)
    with open(log) as f:
        line = f.readline()
        while line:
            print(line)
            try:
                data = alog.parse(line)
                # Only parse finished jobs
                if 'state' in data and data['state']=='exited':
                    results.append(generate_payload(data))
            except Exception as e:
                # Cannot have any exception
                print(e)
                exit(0)
            line = f.readline()

print("Total finished jobs: %d" % len(results))

with open(log_source + ".json", "w") as f:
    json.dump(results, f)

print("Parsed jobs are saved in %s.json" % log_source)