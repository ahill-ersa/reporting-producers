#!/usr/bin/env python

# pylint: disable=broad-except

import re, sys, os, time, uuid
import libvirt
from xml.etree import ElementTree
from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, get_hostname
import json
import os.path

log = getLogger(__name__)

nova_local = ".novalocal"
nova_bridge = "/var/lib/nova/networks/nova-br100.conf"

index = {
    "ncpu" : 3,
    "cpu" : 4,
    "read" : 1,
    "write" : 3,
    "transmit" : 4,
    "receive" : 0
}


def get_devices(dom, type):
    devices = []
    tree = ElementTree.fromstring(dom.XMLDesc(0))
    for target in tree.findall("devices/%s/target" % type):
        dev = target.get("dev")
        if not dev in devices:
            devices.append(dev)
    return devices

def get_network_devices(dom):
    return get_devices(dom, "interface")

def get_disk_devices(dom):
    return get_devices(dom, "disk")

def get_mac(dom):
    return ElementTree.fromstring(dom.XMLDesc(0)).findall("devices/interface/mac")[0].attrib["address"]

def get_name(dom):
    return ElementTree.fromstring(dom.XMLDesc(0)).findall("name")[0].text
    
def load_nova_network():
    mac_map = {}
    if not os.path.exists(nova_bridge) or not os.path.isfile(nova_bridge):
        return None
    with open(nova_bridge, "r") as nova:
        for line in nova:
            line = line.strip().split(",")
            mac = line[0]
            name = line[1]
            if name.endswith(nova_local):
                name = name[:-len(nova_local)]
            mac_map[mac] = { "name" : name, "ip" : line[2] }
    return mac_map


def process(dom, nova_network):
    info = dom.info()
    mac_add=get_mac(dom)
    cpu = (info[index["cpu"]] / 1000000) / info[index["ncpu"]]
    read_kb = 0
    write_kb = 0
    transmit_kb = 0
    receive_kb = 0

    for disk in get_disk_devices(dom):
        stats = dom.blockStats(disk)
        read_kb += stats[index["read"]] / 1024
        write_kb += stats[index["write"]] / 1024

    for interface in get_network_devices(dom):
        stats = dom.interfaceStats(interface)
        transmit_kb += stats[index["transmit"]] / 1024
        receive_kb += stats[index["receive"]] / 1024

    instance = {
            "id" : dom.UUIDString(),
            "mac" : mac_add,
            "cpu" : cpu,
            "read_kb" : read_kb,
            "write_kb" : write_kb,
            "transmit_kb" : transmit_kb,
            "receive_kb" : receive_kb
        }
    if nova_network is not None and mac_add in nova_network:
        mac_map = nova_network[mac_add]
        instance['name']=mac_map["name"]
        instance['ip']=mac_map["ip"]
    else:
        instance['name']=get_name(dom)
    
    return instance

class LibvirtInput(IDataSource):
    def get_data(self, **kwargs):
        #log.debug(libvirt.__dict__)
        conn = libvirt.openReadOnly(None)
        data={}
        nova_network = load_nova_network()
        for domID in conn.listDomainsID():
            dom = conn.lookupByID(domID)
            data[domID]=process(dom, nova_network)
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        return data
