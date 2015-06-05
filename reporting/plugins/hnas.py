#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, get_hostname
import json
import time
import httplib, urllib2, urllib
import ssl
from functools import partial

log = getLogger(__name__)

class fake_ssl:
    wrap_socket = partial(ssl.wrap_socket, ssl_version=ssl.PROTOCOL_TLSv1)

httplib.ssl = fake_ssl

def get_session_headers(host, username, password):
    url_index = 'https://'+host+'/mgr/app/'
    url_login = 'https://'+host+'/mgr/app/j_security_check'
    
    # get session id from home page
    user_data = [('j_username', username), ('j_password', password)]
    response = urllib2.urlopen(url_index)
    log.debug(response.info())
    cookie = response.info().getheader('Set-Cookie').split(';')[0]
    log.debug(cookie)
    #log in
    data = urllib.urlencode(user_data)
    header={'Cookie': cookie}
    log.debug("%s %s" %(header,data))
    req = urllib2.Request(url_login, data, header)
    response = urllib2.urlopen(req)
    cookies=response.info().getheader('Set-Cookie').split(',')
    log.debug(cookies)
    headers={} #"Referer": "https://192.168.20.10/mgr/app/action/storage.VolumeAction/eventsubmit_dogotoview/ignored/f5/true"}
    headers["Cookie"]=cookies[0].strip().split(';')[0]+"; "+cookies[1].strip().split(';')[0]
    return headers

class FileSystemsInput(IDataSource):
    def __init__(self, host, username, password):
        self.__host=host
        self.__username=username
        self.__password=password
    def get_data(self, **kwargs):
        url='https://'+self.__host+'/mgr/app/template/simple%2CDownloadFileSystemsScreen.vm'
        data={}
        data['timestamp'] = int(time.time())
        data['hostname'] = get_hostname()
        headers=get_session_headers(self.__host, self.__username, self.__password)
        request = urllib2.Request(url, None, headers)
        response = urllib2.urlopen(request)
        raw_data=response.read()
        log.debug(raw_data)
        data['filesystems']=[]
        for line in raw_data.split('\n')[1:]:
            if len(line.strip())==0:
                continue
            items=line.split(',')
            data['filesystems'].append({'lable':items[0],'capacity':items[1],'live-fs-used':items[2],'snapshot-used':items[3],'free':items[4]})
        return data
