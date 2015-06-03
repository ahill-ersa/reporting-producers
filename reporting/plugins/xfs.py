#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, list_to_dict, get_hostname
import json
import time

log = getLogger(__name__)

class QuotaReportParser(IParser):
    def __init__(self, exclude_users):
        self.__exclude_users=exclude_users
    def parse(self, data):
        result = {}
        
        result["timestamp"] = int(time.time())
        result["hostname"] = get_hostname()
        result["filesystems"] = []
        
        for line in data.split("\n"):
            line = line.strip()
            tokens = line.split()
        
            if line.startswith("User quota on"):
                filesystem = {
                    "device" : tokens[4][1:-1],
                    "filesystem" : tokens[3],
                    "quota" : []
                }
                result["filesystems"].append(filesystem)
                continue
        
            if line.startswith("User ID") or line.startswith("-") or line.startswith("Blocks") or (len(line) == 0):
                continue
        
            entry = {}
            entry["username"] = tokens[0]
            if entry["username"] in self.__exclude_users:
                continue
            entry["used"] = int(tokens[1])
            entry["soft"] = int(tokens[2])
            entry["hard"] = int(tokens[3])
            filesystem["quota"].append(entry)
        
        return result

class StatParser(IParser):
    def parse(self, data):
        result = {}
        full_names={"extent_alloc":"allocs",
                   "abt":"alloc_btree",
                   "blk_map":"block_map",
                   "bmbt":"bmap_btree",
                   "dir":"dir_ops",
                   "trans":"transactions",
                   "ig":"inode_ops",
                   "push_ail":"log_tail",
                   "qm":"qmstat"
                   }
        variables={"allocs":["alloc_extent", "alloc_block", "free_extent", "free_block"], 
                   "alloc_btree":["lookup","compare","insrec","delrec"],
                   "block_map":["read_ops","write_ops","unmap","add_exlist","del_exlist","look_exlist","cmp_exlist"],
                   "bmap_btree":["lookup","compare","insrec","delrec"],
                   "dir_ops":["lookup","create","remove","getdents"],
                   "transactions":["sync","async","empty"],
                   "inode_ops":["ig_attempts","ig_found","ig_frecycle","ig_missed","ig_dup","ig_reclaims","ig_attrchg"],
                   "log":["writes","blocks","noiclogs","force","force_sleep"],
                   "log_tail":["try_logspace","sleep_logspace","push_ail.pushes","push_ail.success","push_ail.pushbuf","push_ail.pinned","push_ail.locked","push_ail.flushing","push_ail.restarts","push_ail.flush"],
                   "xstrat":["quick","split"],
                   "rw":["xs_write_calls","xs_read_calls"],
                   "attr":["xs_attr_get","xs_attr_set","xs_attr_remove","xs_attr_list"],
                   "icluster":["xs_iflush_count","xs_icluster_flushcnt","xs_icluster_flushinode"],
                   "vnodes":["vn_active","vn_alloc","vn_get","vn_hold","vn_rele","vn_reclaim","vn_remove"],
                   "abtb2":["lookup","compare","insrec","delrec","newroot","killroot","increment","decrement","lshift","rshift","split","join","alloc","free","moves"],
                   "abtc2":["lookup","compare","insrec","delrec","newroot","killroot","increment","decrement","lshift","rshift","split","join","alloc","free","moves"],
                   "bmbt2":["lookup","compare","insrec","delrec","newroot","killroot","increment","decrement","lshift","rshift","split","join","alloc","free","moves"],
                   "ibt2":["lookup","compare","insrec","delrec","newroot","killroot","increment","decrement","lshift","rshift","split","join","alloc","free","moves"],
                   "qmstat":["dqreclaims","dqreclaim_misses","dquot_dups","dqcachemisses","dqcachehits","dqwants"],
                   "buf":["xb_get","xb_create","xb_get_locked","xb_get_locked_waited","xb_busy_locked","xb_miss_locked","xb_page_retries","xb_page_found","xb_get_read"],
                   "xpc":["xs_xstrat_bytes","xs_write_bytes","xs_read_bytes"]}
        result["timestamp"] = int(time.time())
        result["hostname"] = get_hostname()
        result["xfs"] = {}
        lines=data.split("\n")
        for i in range(0,len(lines)-1):
            values=lines[i].split(' ')
            cat_name=values[0]
            if cat_name in full_names:
                cat_name=full_names[cat_name]
            if cat_name in variables:
                result["xfs"][cat_name]={}
                for j in range(0,len(variables[cat_name])):
                    #print variables[cat_name][j]
                    result["xfs"][cat_name][variables[cat_name][j]]=values[j+1]
            #else:
            #    print cat_name+" not found"
        result["xfs"]['debug']=lines[-1].split(' ')[1]
        
        return result
