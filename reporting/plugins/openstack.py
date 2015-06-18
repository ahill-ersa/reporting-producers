#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, init_message
import json
import time
import copy

log = getLogger(__name__)

class NovaListInput(IDataSource):
    def __init__(self, project, username, password, auth_url):
        self.__project=project
        self.__username=username
        self.__password=password
        self.__auth_url=auth_url
    def get_data(self, **kwargs):
        data=init_message()
        data['instances']=[]
        from novaclient.v1_1 import client
        conn=client.Client(self.__username, self.__password, self.__project, self.__auth_url, service_type='compute')
        conn.authenticate()
        servers = conn.servers.list(search_opts={'all_tenants':1})
        for server in servers:
            data['instances'].append(server._info)
        return data
    
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
        tenants=keystone.tenants.list()
        for tenant in tenants:
            data['tenants'].append(tenant._info)
        users=keystone.users.list()
        for user in users:
            data['users'].append(user._info)
        return data
