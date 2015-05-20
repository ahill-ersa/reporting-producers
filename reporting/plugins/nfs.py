#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, list_to_dict, get_hostname
import json
import time

log = getLogger(__name__)

class MountstatsParser(IParser):
    def __init__(self, fstype):
        self.__fstype=fstype
    def parse(self, data):
        result = {}
        result["timestamp"] = int(time.time())
        result["hostname"] = get_hostname()
        key = ''
        for line in data.split("\n"):
            words = line.split()
            if len(words) == 0:
                continue
            if words[0] == 'device':
                if not words[7] in self.__fstype:
                    continue
                key = words[4]
                new = [ line.strip() ]
            elif 'nfs' in words or 'nfs4' in words:
                key = words[3]
                new = [ line.strip() ]
            else:
                new += [ line.strip() ]
            stats = DeviceData()
            stats.parse_stats(new)
            result[key] = stats.raw()
        return result


def difference(x, y):
    """Used for a map() function
    """
    return x - y

class DeviceData:
    """DeviceData objects provide methods for parsing and displaying
    data for a single mount grabbed from /proc/self/mountstats
    """
    def __init__(self):
        self.__nfs_data = dict()
        self.__rpc_data = dict()
        self.__rpc_data['ops'] = []

    def raw(self):
        ops = self.__rpc_data["ops"]
        self.__rpc_data["ops"] = dict()
        for op in ops:
            stats = self.__rpc_data[op]
            named_stats = dict()
            named_stats["ops"] = stats[0]
            named_stats["retransmissions"] = stats[1] - stats[0]
            named_stats["major_timeouts"] = stats[2]
            named_stats["bytes_sent"] = stats[3]
            named_stats["bytes_received"] = stats[4]
            named_stats["backlog_wait"] = stats[5]
            named_stats["total_rtt"] = stats[6]
            named_stats["total_execute_time"] = stats[7]
            self.__rpc_data["ops"][op] = named_stats
            self.__rpc_data.pop(op)

        return { "nfs" : self.__nfs_data, "rpc" : self.__rpc_data }

    def __parse_nfs_line(self, words):
        if words[0] == 'device':
            self.__nfs_data['export'] = words[1]
            self.__nfs_data['mountpoint'] = words[4]
            self.__nfs_data['fstype'] = words[7]
            if words[7].find('nfs') != -1:
                self.__nfs_data['statvers'] = words[8]
        elif 'nfs' in words or 'nfs4' in words:
            self.__nfs_data['export'] = words[0]
            self.__nfs_data['mountpoint'] = words[3]
            self.__nfs_data['fstype'] = words[6]
            if words[6].find('nfs') != -1:
                self.__nfs_data['statvers'] = words[7]
        elif words[0] == 'age:':
            self.__nfs_data['age'] = int(words[1])
        elif words[0] == 'opts:':
            self.__nfs_data['mountoptions'] = ''.join(words[1:]).split(',')
        elif words[0] == 'caps:':
            self.__nfs_data['servercapabilities'] = ''.join(words[1:]).split(',')
        elif words[0] == 'nfsv4:':
            self.__nfs_data['nfsv4flags'] = ''.join(words[1:]).split(',')
        elif words[0] == 'sec:':
            keys = ''.join(words[1:]).split(',')
            self.__nfs_data['flavor'] = int(keys[0].split('=')[1])
            self.__nfs_data['pseudoflavor'] = 0
            if self.__nfs_data['flavor'] == 6:
                self.__nfs_data['pseudoflavor'] = int(keys[1].split('=')[1])
        elif words[0] == 'events:':
            self.__nfs_data['inoderevalidates'] = int(words[1])
            self.__nfs_data['dentryrevalidates'] = int(words[2])
            self.__nfs_data['datainvalidates'] = int(words[3])
            self.__nfs_data['attrinvalidates'] = int(words[4])
            self.__nfs_data['syncinodes'] = int(words[5])
            self.__nfs_data['vfsopen'] = int(words[6])
            self.__nfs_data['vfslookup'] = int(words[7])
            self.__nfs_data['vfspermission'] = int(words[8])
            self.__nfs_data['vfsreadpage'] = int(words[9])
            self.__nfs_data['vfsreadpages'] = int(words[10])
            self.__nfs_data['vfswritepage'] = int(words[11])
            self.__nfs_data['vfswritepages'] = int(words[12])
            self.__nfs_data['vfsreaddir'] = int(words[13])
            self.__nfs_data['vfsflush'] = int(words[14])
            self.__nfs_data['vfsfsync'] = int(words[15])
            self.__nfs_data['vfslock'] = int(words[16])
            self.__nfs_data['vfsrelease'] = int(words[17])
            self.__nfs_data['setattrtrunc'] = int(words[18])
            self.__nfs_data['extendwrite'] = int(words[19])
            self.__nfs_data['sillyrenames'] = int(words[20])
            self.__nfs_data['shortreads'] = int(words[21])
            self.__nfs_data['shortwrites'] = int(words[22])
            self.__nfs_data['delay'] = int(words[23])
        elif words[0] == 'bytes:':
            self.__nfs_data['normalreadbytes'] = int(words[1])
            self.__nfs_data['normalwritebytes'] = int(words[2])
            self.__nfs_data['directreadbytes'] = int(words[3])
            self.__nfs_data['directwritebytes'] = int(words[4])
            self.__nfs_data['serverreadbytes'] = int(words[5])
            self.__nfs_data['serverwritebytes'] = int(words[6])

    def __parse_rpc_line(self, words):
        if words[0] == 'RPC':
            self.__rpc_data['statsvers'] = float(words[3])
            self.__rpc_data['programversion'] = words[5]
        elif words[0] == 'xprt:':
            self.__rpc_data['protocol'] = words[1]
            if words[1] == 'udp':
                self.__rpc_data['port'] = int(words[2])
                self.__rpc_data['bind_count'] = int(words[3])
                self.__rpc_data['rpcsends'] = int(words[4])
                self.__rpc_data['rpcreceives'] = int(words[5])
                self.__rpc_data['badxids'] = int(words[6])
                self.__rpc_data['inflightsends'] = int(words[7])
                self.__rpc_data['backlogutil'] = int(words[8])
            elif words[1] == 'tcp':
                self.__rpc_data['port'] = words[2]
                self.__rpc_data['bind_count'] = int(words[3])
                self.__rpc_data['connect_count'] = int(words[4])
                self.__rpc_data['connect_time'] = int(words[5])
                self.__rpc_data['idle_time'] = int(words[6])
                self.__rpc_data['rpcsends'] = int(words[7])
                self.__rpc_data['rpcreceives'] = int(words[8])
                self.__rpc_data['badxids'] = int(words[9])
                self.__rpc_data['inflightsends'] = int(words[10])
                self.__rpc_data['backlogutil'] = int(words[11])
            elif words[1] == 'rdma':
                self.__rpc_data['port'] = words[2]
                self.__rpc_data['bind_count'] = int(words[3])
                self.__rpc_data['connect_count'] = int(words[4])
                self.__rpc_data['connect_time'] = int(words[5])
                self.__rpc_data['idle_time'] = int(words[6])
                self.__rpc_data['rpcsends'] = int(words[7])
                self.__rpc_data['rpcreceives'] = int(words[8])
                self.__rpc_data['badxids'] = int(words[9])
                self.__rpc_data['backlogutil'] = int(words[10])
                self.__rpc_data['read_chunks'] = int(words[11])
                self.__rpc_data['write_chunks'] = int(words[12])
                self.__rpc_data['reply_chunks'] = int(words[13])
                self.__rpc_data['total_rdma_req'] = int(words[14])
                self.__rpc_data['total_rdma_rep'] = int(words[15])
                self.__rpc_data['pullup'] = int(words[16])
                self.__rpc_data['fixup'] = int(words[17])
                self.__rpc_data['hardway'] = int(words[18])
                self.__rpc_data['failed_marshal'] = int(words[19])
                self.__rpc_data['bad_reply'] = int(words[20])
        elif words[0] == 'per-op':
            self.__rpc_data['per-op'] = words
        else:
            op = words[0][:-1]
            self.__rpc_data['ops'] += [op]
            self.__rpc_data[op] = [int(word) for word in words[1:]]

    def parse_stats(self, lines):
        """Turn a list of lines from a mount stat file into a
        dictionary full of stats, keyed by name
        """
        found = False
        for line in lines:
            words = line.split()
            if len(words) == 0:
                continue
            if (not found and words[0] != 'RPC'):
                self.__parse_nfs_line(words)
                continue

            found = True
            self.__parse_rpc_line(words)

    def is_nfs_mountpoint(self):
        """Return True if this is an NFS or NFSv4 mountpoint,
        otherwise return False
        """
        if self.__nfs_data['fstype'] == 'nfs':
            return True
        elif self.__nfs_data['fstype'] == 'nfs4':
            return True
        return False

    def display_nfs_options(self):
        """Pretty-print the NFS options
        """
        print('Stats for %s mounted on %s:' % \
            (self.__nfs_data['export'], self.__nfs_data['mountpoint']))

        print('  NFS mount options: %s' % ','.join(self.__nfs_data['mountoptions']))
        print('  NFS server capabilities: %s' % ','.join(self.__nfs_data['servercapabilities']))
        if 'nfsv4flags' in self.__nfs_data:
            print('  NFSv4 capability flags: %s' % ','.join(self.__nfs_data['nfsv4flags']))
        if 'pseudoflavor' in self.__nfs_data:
            print('  NFS security flavor: %d  pseudoflavor: %d' % \
                (self.__nfs_data['flavor'], self.__nfs_data['pseudoflavor']))
        else:
            print('  NFS security flavor: %d' % self.__nfs_data['flavor'])

    def display_nfs_events(self):
        """Pretty-print the NFS event counters
        """
        print()
        print('Cache events:')
        print('  data cache invalidated %d times' % self.__nfs_data['datainvalidates'])
        print('  attribute cache invalidated %d times' % self.__nfs_data['attrinvalidates'])
        print('  inodes synced %d times' % self.__nfs_data['syncinodes'])
        print()
        print('VFS calls:')
        print('  VFS requested %d inode revalidations' % self.__nfs_data['inoderevalidates'])
        print('  VFS requested %d dentry revalidations' % self.__nfs_data['dentryrevalidates'])
        print()
        print('  VFS called nfs_readdir() %d times' % self.__nfs_data['vfsreaddir'])
        print('  VFS called nfs_lookup() %d times' % self.__nfs_data['vfslookup'])
        print('  VFS called nfs_permission() %d times' % self.__nfs_data['vfspermission'])
        print('  VFS called nfs_file_open() %d times' % self.__nfs_data['vfsopen'])
        print('  VFS called nfs_file_flush() %d times' % self.__nfs_data['vfsflush'])
        print('  VFS called nfs_lock() %d times' % self.__nfs_data['vfslock'])
        print('  VFS called nfs_fsync() %d times' % self.__nfs_data['vfsfsync'])
        print('  VFS called nfs_file_release() %d times' % self.__nfs_data['vfsrelease'])
        print()
        print('VM calls:')
        print('  VFS called nfs_readpage() %d times' % self.__nfs_data['vfsreadpage'])
        print('  VFS called nfs_readpages() %d times' % self.__nfs_data['vfsreadpages'])
        print('  VFS called nfs_writepage() %d times' % self.__nfs_data['vfswritepage'])
        print('  VFS called nfs_writepages() %d times' % self.__nfs_data['vfswritepages'])
        print()
        print('Generic NFS counters:')
        print('  File size changing operations:')
        print('    truncating SETATTRs: %d  extending WRITEs: %d' % \
            (self.__nfs_data['setattrtrunc'], self.__nfs_data['extendwrite']))
        print('  %d silly renames' % self.__nfs_data['sillyrenames'])
        print('  short reads: %d  short writes: %d' % \
            (self.__nfs_data['shortreads'], self.__nfs_data['shortwrites']))
        print('  NFSERR_DELAYs from server: %d' % self.__nfs_data['delay'])

    def display_nfs_bytes(self):
        """Pretty-print the NFS event counters
        """
        print()
        print('NFS byte counts:')
        print('  applications read %d bytes via read(2)' % self.__nfs_data['normalreadbytes'])
        print('  applications wrote %d bytes via write(2)' % self.__nfs_data['normalwritebytes'])
        print('  applications read %d bytes via O_DIRECT read(2)' % self.__nfs_data['directreadbytes'])
        print('  applications wrote %d bytes via O_DIRECT write(2)' % self.__nfs_data['directwritebytes'])
        print('  client read %d bytes via NFS READ' % self.__nfs_data['serverreadbytes'])
        print('  client wrote %d bytes via NFS WRITE' % self.__nfs_data['serverwritebytes'])

    def display_rpc_generic_stats(self):
        """Pretty-print the generic RPC stats
        """
        sends = self.__rpc_data['rpcsends']

        print()
        print('RPC statistics:')

        print('  %d RPC requests sent, %d RPC replies received (%d XIDs not found)' % \
            (sends, self.__rpc_data['rpcreceives'], self.__rpc_data['badxids']))
        if sends != 0:
            print('  average backlog queue length: %d' % \
                (float(self.__rpc_data['backlogutil']) / sends))

    def compare_iostats(self, old_stats):
        """Return the difference between two sets of stats
        """
        result = DeviceData()

        # copy self into result
        for key, value in self.__nfs_data.items():
            result.__nfs_data[key] = value
        for key, value in self.__rpc_data.items():
            result.__rpc_data[key] = value

        # compute the difference of each item in the list
        # note the copy loop above does not copy the lists, just
        # the reference to them.  so we build new lists here
        # for the result object.
        for op in result.__rpc_data['ops']:
            result.__rpc_data[op] = list(map(difference, self.__rpc_data[op], old_stats.__rpc_data[op]))

        # update the remaining keys we care about
        result.__rpc_data['rpcsends'] -= old_stats.__rpc_data['rpcsends']
        result.__rpc_data['backlogutil'] -= old_stats.__rpc_data['backlogutil']
        result.__nfs_data['serverreadbytes'] -= old_stats.__nfs_data['serverreadbytes']
        result.__nfs_data['serverwritebytes'] -= old_stats.__nfs_data['serverwritebytes']

        return result

