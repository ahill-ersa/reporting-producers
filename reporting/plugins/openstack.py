#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, init_message
import json
import time
import copy
import uuid

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
            if 'tenantId' not in user._info:
                log.debug("user %s doesn't have tenant Id."%user._info['name'])
        tenants=keystone.tenants.list()
        for tenant in tenants:
            tenant_info = tenant._info
            if tenant_info['description'] and 'personal tenancy' not in tenant_info['description'].lower():
                tenant_info['users'] = [{ 'id' : user._info['id'], 'username' : user._info['username']} for user in users if 'tenantId' in user._info and user._info['tenantId']==tenant_info['id']]
            data['tenants'].append(tenant_info)
        return data
