#!/usr/bin/env python

# pylint: disable=broad-except

import socket, sys, json, pprint

socket_file="/var/run/reporting-producer/producer.sock"

def main(argv):
    csock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    csock.connect(socket_file)
    #print csock
    print "sending command %s..."%argv[0]
    csock.sendall(argv[0]+"\n")
    buffer=[]
    while True:
        data = csock.recv(16)
        if data:
            buffer.append(data)
        else:
            break
    csock.close()
    output=json.loads(''.join(buffer))
    if 'system' in output:
        print output['system']
        sys.exit(0)
    pprint.pprint(output)

if __name__ == "__main__":
    main(sys.argv[1:])