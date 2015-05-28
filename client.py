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
    if 'collectors' in output:
        if len(argv)>1:
            cols=[c for c in output['collectors'] if c['name']==argv[1]]
            if len(cols)>0:
                show_full_data=False
                if len(argv)>2 and argv[2]=='-d':
                    show_full_data=True
                print_detail(cols[0], show_full_data)
            else:
                print "collector %s not found." % argv[1]
            sys.exit(0)
        print_collectors(output['collectors'])
        sys.exit(0)
    if 'producer-config' in output:
        print json.dumps(output['producer-config'], indent=4, sort_keys=True)
        sys.exit(0)
    pprint.pprint(output)

def print_collectors(collectors):
    print "Number of collectors: %d" % len(collectors)
    template = "{0:25}{1:40}{2:^8}{3:^40}{4:^45}{5:^11}{6:^20}{7:^8}{8:^14}{9:^11}{10:^12}{11:^11}{12:^12}{13:^12}"
    print template.format("Name", "Session ID", "Running", "Input", "Parser", "Output", "Schema", "Version", "Msg_Collected", 
                          "Msg_Failed", "Sleep_Count", "Sleep_Time", "Error_Count", "Max_Errors")
    print '='*269
    for collector in collectors:
        input=collector['config']['input']['type']
        if collector['config']['input']['type']=='class':
            input=collector['config']['input']['name']
        parser=""
        if 'parser' in collector['config']:
            if collector['config']['parser']['type']=='class':
                parser=collector['config']['parser']['name']
            else:
                parser=collector['config']['parser']['type']
        print template.format(collector['name'], collector['session_id'], collector['is_running'], input, 
                              parser, collector['config']['output'], collector['config']['metadata']['schema'],collector['config']['metadata']['version'],
                              collector['number_collected'], collector['number_failed'],collector['sleep_count'], collector['sleep_time'], 
                              collector['error_count'], collector['max_error_count'])
    
def print_detail(collector, show_full_data):
    template="{0:32}{1:}"
    print template.format("Name:", collector['name'])
    print template.format("Session ID:", collector['session_id'])
    print template.format("Running:", collector['is_running'])
    print template.format("Number of messages collected:", collector['number_collected'])
    print template.format("Number of messages failed:", collector['number_failed'])
    print template.format("Sleep Count:", collector['sleep_count'])
    print template.format("Sleep Time:", collector['sleep_time'])
    print template.format("Consecutive Error Count:", collector['error_count'])
    print template.format("Maximum Consecutive Errors:", collector['max_error_count'])
    print "Config:"
    print "\tInput:"
    template1="{0:16}{1:16}{2:}"
    for k,v in collector['config']['input'].iteritems():
        print template1.format(' ',"%s:"%k, v)
    if 'parser' in collector['config']:
        print '\tParser:'
        for k,v in collector['config']['parser'].iteritems():
            print template1.format(' ',"%s:"%k, v)
    print "\tOutput: %s"%collector['config']['output']
    if 'tailer' in collector:
        print "Tailer:"
        for k,v in collector['tailer'].iteritems():
            print template1.format(' ',"%s:"%k, v)
    current_data=''
    if collector['current_data'] is not None:
        if isinstance(collector['current_data'], list):
            print "Current Data:"
            for line in collector['current_data']:
                if show_full_data:
                    print '\t%s' % line.strip()
                else:
                    print '\t%s' % line.strip()[:256]
        else:       
            if show_full_data:
                print template.format("Current Data:", collector['current_data'])
            else:
                print template.format("Current Data:", collector['current_data'][:256])
    
if __name__ == "__main__":
    if len(sys.argv)<2:
        print "Run \"%s help\" to get help message." % sys.argv[0]
        sys.exit(1)
    main(sys.argv[1:])