#!/usr/bin/env python

import platform, re, sys, os, time, libvirt, uuid, json
from xml.etree import ElementTree

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

def load_nova_network():
    mac_map = {}
    with open(nova_bridge, "r") as nova:
        for line in nova:
            line = line.strip().split(",")
            mac = line[0]
            name = line[1]
            if name.endswith(nova_local):
                name = name[:-len(nova_local)]
            mac_map[mac] = { "name" : name, "ip" : line[2] }
    return mac_map

host = platform.node()
hostname_splitter = re.compile("[-.]")

conn = libvirt.openReadOnly(None)

def process(dom, nova_network):
    info = dom.info()
    cpu = (info[index["cpu"]] / 1000000) / info[index["ncpu"]]
    mac_map = nova_network[get_mac(dom)]
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

    data = {
        "schema" : "libvirt",
        "version" : 1,
        "host" : host,
        "data" : {
            "id" : dom.UUIDString(),
            "name" : mac_map["name"],
            "ip" : mac_map["ip"]
            "cpu" : cpu,
            "read_kb" = read_kb,
            "write_kb" = write_kb,
            "transmit_kb" = transmit_kb,
            "receive_kb" = receive_kb
        },
        "id" : str(uuid.uuid4()),
        "timestamp" : int(time.time())
    }

    print json.dumps(data)

while True:
    nova_network = load_nova_network()
    for domID in conn.listDomainsID():
        dom = conn.lookupByID(domID)
        process(dom, nova_network)
    time.sleep(20)
