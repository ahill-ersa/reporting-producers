#!/usr/bin/env python

import argparse, base64, hashlib, json, os, platform, time, uuid

from argparse import RawTextHelpFormatter

import requests

def main(host, tenant, username, password):
    username = base64.b64encode(username)
    password = hashlib.md5(password).hexdigest()

    headers = {
        "Authorization" : "HCP %s:%s" % (username, password),
        "Accept" : "application/json"
    }

    url = "https://%s:9090/mapi/tenants/%s/chargebackReport" % (host, tenant)

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        data = {}
        data["id"] = str(uuid.uuid4())
        data["timestamp"] = int(time.time())
        data["hostname"] = platform.node()
        data["schema"] = "hcp-chargeback"
        data["version"] = 1
        data["hcp-chargeback"] = response.json()["chargebackData"]
        print json.dumps(data)
    else:
        print "Error: HTTP response code:", response.status_code
        exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description = "Fetch HCP chargeback data",
        epilog = "Required environment variables: HCP_USERNAME and HCP_PASSWORD.",
        formatter_class = RawTextHelpFormatter)
    parser.add_argument("-H", "--host", help="Hostname", required=True)
    parser.add_argument("-t", "--tenant", help="Tenant", required=True)

    args = parser.parse_args()

    username = os.getenv("HCP_USERNAME")
    password = os.getenv("HCP_PASSWORD")
    if (username is None) or (password is None):
        parser.print_help()
        exit(1)

    main(args.host, args.tenant, username, password)
