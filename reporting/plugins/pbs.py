#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, list_to_dict, get_hostname
from reporting.outputs import IOutput
import json
import time
import os

log = getLogger(__name__)

class MomLogParser(IParser):
    def parse(self, data):
        tokens = [x.lower().strip() for x in data.split(";")]
        data={}
        data["timestamp"] = int(time.mktime(time.strptime(tokens[0], "%m/%d/%Y %H:%M:%S")))
        data["hostname"] = get_hostname()
    
        event_type = tokens[3]
        data['event_type']=event_type
    
        if event_type == "svr":
            data['svr_type']=tokens[4]
            data['event_description']=tokens[5]
        elif event_type == "job":
            data['jobid']=tokens[4]
            data['event_description']=tokens[5]
            if data['jobid']=="tmomfinalizejob3":
                data['jobid']=tokens[5].split(" ")[1]
        return data

class ServerLogParser(IParser):
    def parse(self, data):
        tokens = [x.lower().strip() for x in data.split(";")]
        data={}
        data["timestamp"] = int(time.mktime(time.strptime(tokens[0], "%m/%d/%Y %H:%M:%S")))
        data["hostname"] = get_hostname()
    
        event_type = tokens[3]
        data['event_type']=event_type
    
        if event_type == "req":
            if len(tokens[4])>0:
                data['req_type']=tokens[4]
            data['event_description']=tokens[5]
        elif event_type == "svr":
            data['svr_type']=tokens[4]
            data['event_description']=tokens[5]
            event_description=tokens[5]
            if "job nanny" in event_description:
                # example
                # 08/06/2014 01:03:59;0001;PBS_Server;Svr;PBS_Server;LOG_ERROR::job nanny, exiting job '786299.tizard1' still exists, sending a SIGKILL
                data["jobid"] = event_description.split("'")[1]
        elif event_type == "job":
            jobid=tokens[4]
            if jobid == 'NULL':
                data['event_description']=tokens[5]
            else:
                if not jobid.split('.')[0].split('[')[0].isdigit():
                    data['action_type']=tokens[4]
                    jobid=tokens[5]
                    if not jobid.split('.')[0].split('[')[0].isdigit():
                        data['event_description']=tokens[5]
                    else:
                        data['jobid']=jobid
                        data['event_description']=tokens[6]
                else:
                    data['jobid']=jobid
                    data['event_description']=tokens[5]
                event_description=data['event_description']
                if event_description.startswith('exit_status'):
                    # example (split)
                    # 08/06/2014 00:29:47;0010;PBS_Server;Job;796694.tizard1;Exit_status=0 resources_used.cput=18:25:07
                    # resources_used.mem=2569184kb resources_used.vmem=14061332kb resources_used.walltime=02:59:47
                    data["stats"] = {}
                    stats = event_description.split()
                    #print stats
                    for stat in stats:
                        stat = stat.split("=")
                        #print stat
                        if "." in stat[0]:
                            stat[0] = stat[0].split(".")
                        if reduce(lambda x, y: x and y, [str.isdigit(_) for _ in stat[1]]):
                            stat[1] = int(stat[1])
        
                        if isinstance(stat[0], str):
                            data["stats"][stat[0]] = stat[1]
                        elif isinstance(stat[0], list):
                            list_to_dict(data["stats"], stat[0], stat[1])
                elif 'job queued' in event_description:
                    # example (split)
                    # 08/06/2014 00:44:15;0008;PBS_Server;Job;796871.tizard1;Job Queued at request of foo@tizard1,
                    # owner = foo@tizard1, job name = something.sh, queue = gtx
                    data["attributes"] = {}
                    for kv in event_description.split(",")[1:]:
                        kv = kv.split("=")
                        kv = [_.strip() for _ in kv]
                        data["attributes"][kv[0].replace(" ", "_")] = kv[1]
                        if "owner" in data["attributes"]:
                            data["attributes"]["owner"] = data["attributes"]["owner"].split("@")[0]
    
        return data

class AccountingLogParser(IParser):
    def parse(self, data):
        tokens = [x.lower().strip() for x in data.split(";")]
        data={}
        data["timestamp"] = int(time.mktime(time.strptime(tokens[0], "%m/%d/%Y %H:%M:%S")))
        data["hostname"] = get_hostname()
    
        job_states = {
            "r" : "run",
            "s" : "started",
            "q" : "queued",
            "e" : "exited",
            "d" : "deleted"
        }
        for state in job_states:
            if state == tokens[1]:
                data["state"] = job_states[state]
                break
        
        data["jobid"] = tokens[2]
    
        for attr in tokens[3].split():
            kv = attr.split("=")
            try:     
                if reduce(lambda x, y: x and y, [str.isdigit(_) for _ in kv[1]]):
                    kv[1] = int(kv[1])
                elif kv[0] == "exec_host":
                    hosts = {}
                    for slot in kv[1].split("+"):
                        slot = slot.split("/")
                        if slot[0] not in hosts:
                            hosts[slot[0]] = []
                        if slot[1].isdigit():
                            hosts[slot[0]].append(int(slot[1]))
                        elif '-' in slot[1]:
                            start_end=slot[1].split('-')
                            hosts[slot[0]].extend(range(int(start_end[0]), int(start_end[1])+1))
                    kv[1] = hosts
                elif kv[0] == "owner":
                    kv[1] = kv[1].split("@")[0]
                if "." in kv[0]:
                    kv[0] = kv[0].split(".")
    
                if isinstance(kv[0], str):
                    data[kv[0]] = kv[1]
                elif isinstance(kv[0], list):
                    list_to_dict(data, kv[0], kv[1])
            except Exception as ERROR:
                log.debug(ERROR)
                pass
        return data

class AccountingCsvOutput(IOutput):
    def __init__(self, path):
        self.__path = path
        self.__handle=open(self.__path, "w")
        self.__data={}
        
    def push(self, data):
        if not isinstance(data, list):
            data = [data]
        for item in data:
            if 'user' in item['data']:
                username=item['data']['user']
                if item['data']['state']=='exited':
                    if username not in self.__data:
                        self.__data[username]={'num_jobs':0, 'hours':0}
                    walltime=item['data']['resources_used']['walltime'].split(':')
                    cores=sum(len(c) for h,c in item['data']['exec_host'].iteritems())
                    hours=(float(walltime[0])+float(walltime[1])/60+float(walltime[2])/3600)*cores
                    log.debug('data %s cores %s walltime %s hours %s' %(item, cores, walltime, hours))
                    self.__data[username]['num_jobs']+=1
                    self.__data[username]['hours']+=hours
        log.debug("writing data to file %s" % self.__path)
        self.__handle.seek(0)
        self.__handle.write("username,Number of Jobs,Hours" + os.linesep)
        for k,v in self.__data.iteritems():
            self.__handle.write("%s,%d,%.2f"%(k,v['num_jobs'],v['hours']) + os.linesep)
        self.__handle.flush()
        
    def close(self):
        log.debug("closing file handle for %s" % self.__path)
        if self.__handle:
            self.__handle.close()
