#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, init_message
import json
import time
import copy
import uuid
import random
from multiprocessing.pool import ThreadPool
import requests

log = getLogger(__name__)

class NovaListInput(IDataSource):
    def __init__(self, project, username, password, auth_url, number_per_page=500):
        self.__project=project
        self.__username=username
        self.__password=password
        self.__auth_url=auth_url
        self.__number_per_page=number_per_page
    def get_data(self, **kwargs):
        query_id=str(uuid.uuid4())
        data_list=[]
        from novaclient import client
        conn=client.Client(2, self.__username, self.__password, self.__project, self.__auth_url)
        servers = conn.servers.list(search_opts={'all_tenants':1}, limit=self.__number_per_page)
        while len(servers)>0:
            log.debug("Got %d instances, first id %s" % (len(servers), servers[0].id))
            data=init_message()
            data['query_id']=query_id
            data['flavors']=[f._info for f in conn.flavors.list()]
            data['instances']=[]
            for server in servers:
                data['instances'].append(server._info)
            data_list.append(data)
            last_id=servers[-1].id
            log.debug("last_id %s" %last_id)
            servers = conn.servers.list(search_opts={'all_tenants':1}, marker=last_id, limit=self.__number_per_page)
        return data_list
    
class KeystoneListInput(IDataSource):
    def __init__(self, project, username, password, auth_url):
        self.__project=project
        self.__username=username
        self.__password=password
        self.__auth_url=auth_url
    def get_data(self, **kwargs):
        data=init_message()
        copy_attributes=['OS-EXT-STS:task_state', 'addresses', 'OS-EXT-STS:vm_state', 'OS-EXT-SRV-ATTR:instance_name', 'OS-SRV-USG:launched_at',
                         'id', 'security_groups', 'user_id', 'OS-DCF:diskConfig', 'accessIPv4', 'accessIPv6', 'progress', 'OS-EXT-STS:power_state',
                         'OS-EXT-AZ:availability_zone', 'config_drive', 'status', 'updated', 'hostId', 'OS-EXT-SRV-ATTR:host', 'OS-SRV-USG:terminated_at',
                         'key_name', 'OS-EXT-SRV-ATTR:hypervisor_hostname', 'name', 'created', 'tenant_id', 'os-extended-volumes:volumes_attached',
                         'fault', 'metadata']
        data['tenants']=[]
        data['users']=[]
        from keystoneclient.v2_0 import client

        keystone=client.Client(username=self.__username, password=self.__password, tenant_name=self.__project, auth_url=self.__auth_url)
        users=keystone.users.list()
        for user in users:
            data['users'].append(user._info)
        tenants=keystone.tenants.list()
        for tenant in tenants:
            tenant_info = tenant._info
            if tenant_info['description'] and 'personal tenancy' not in tenant_info['description'].lower():
                membership_retrieved = False
                membership_attempt = 0
                while not membership_retrieved and membership_attempt < 3:
                    try:
                        tenant_info['users'] = [{'id' : user.id, 'username' : user.username} for user in tenant.list_users()]
                        membership_retrieved = True
                    except:
                        time.sleep(2 ** membership_attempt)
                        membership_attempt += 1
            data['tenants'].append(tenant_info)
        return data

class CinderListInput(IDataSource):
    def __init__(self, project, username, password, auth_url, number_per_page=500):
        self.__project=project
        self.__username=username
        self.__password=password
        self.__auth_url=auth_url
        self.__number_per_page=number_per_page
    def get_data(self, **kwargs):
        query_id=str(uuid.uuid4())
        data_list=[]
        from cinderclient import client
        conn=client.Client(2, self.__username, self.__password, self.__project, self.__auth_url)
        
        volumes = conn.volumes.list(search_opts={'all_tenants':1}, limit=self.__number_per_page)
        while len(volumes)>0:
            log.debug("Got %d volumes, first id %s" % (len(volumes), volumes[0].id))
            data=init_message()
            data['query_id']=query_id
            data['volumes']=[]
            for volume in volumes:
                data['volumes'].append(volume._info)
            data_list.append(data)
            last_id=volumes[-1].id
            log.debug("last_id %s" %last_id)
            volumes = conn.volumes.list(search_opts={'all_tenants':1}, marker=last_id, limit=self.__number_per_page)
            
        volume_snapshots = conn.volume_snapshots.list(search_opts={'all_tenants':1})
        log.debug("Got %d volume_snapshots" % len(volume_snapshots))
        data=init_message()
        data['query_id']=query_id
        data['volume_snapshots']=[]
        for volume in volume_snapshots:
            data['volume_snapshots'].append(volume._info)
        data_list.append(data)

        return data_list

class SwiftUsageInput(IDataSource):
    def __init__(self, project, username, password, auth_url, ring_location="/etc/swift/account.ring.gz"):
        self.__project=project
        self.__username=username
        self.__password=password
        self.__auth_url=auth_url
        self.__ring_location=ring_location
        self.__ring=None
    def get_data(self, **kwargs):
        query_id=str(uuid.uuid4())
        data_list=[]
        from keystoneclient.v2_0 import client
        from swift.common.ring import Ring
        keystone=client.Client(username=self.__username, password=self.__password, tenant_name=self.__project, auth_url=self.__auth_url)
        self.__ring = Ring(self.__ring_location)
        tenants = [tenant.id for tenant in keystone.tenants.list()]
        random.shuffle(tenants)
        data=init_message()
        for tenant, stats in zip(tenants, ThreadPool().map(self.fetch, tenants)):
            if stats is not None:
                data[tenant] = stats
        return data
        
    def fetch(self, tenant):
        account = "AUTH_%s" % tenant
        partition = self.__ring.get_part(account, None, None)
        nodes = self.__ring.get_part_nodes(partition)
        random.shuffle(nodes)
        for node in nodes:
            url = "http://%s:%s/%s/%s/%s" % (node["ip"], node["port"], node["device"], partition, account)
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 204:
                    return {
                        "containers" : int(response.headers["x-account-container-count"]),
                        "objects" : int(response.headers["x-account-object-count"]),
                        "bytes" : int(response.headers["x-account-bytes-used"]),
                        "quota" : int(response.headers["x-account-meta-quota-bytes"]) if "x-account-meta-quota-bytes" in response.headers else None
                    }
                elif response.status_code == 404:
                    return None
                else:
                    log.warning("error fetching %s [HTTP %s]", url, response.status_code)
            except:
                log.warning("error fetching %s", url, exc_info=True)
        log.error("failed to fetch info for tenant %s", tenant)
        return None
    