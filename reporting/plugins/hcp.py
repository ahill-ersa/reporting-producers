#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.parsers import IParser
from reporting.collectors import IDataSource
from reporting.utilities import getLogger, get_hostname, init_message
import json
import time, datetime
import httplib, urllib2, urllib
import base64
import hashlib
from reporting.exceptions import InputDataError, RemoteServerError

log = getLogger(__name__)

class ChargeBackInput(IDataSource):
    def __init__(self, host, username, password, query_period=1):
        self.__host=host
        self.__username=username
        self.__password=password
        self.__query_period=query_period
    def get_data(self, **kwargs):
        data=init_message()

        username = base64.b64encode(self.__username)
        password = hashlib.md5(self.__password).hexdigest()
        
        headers = { "Authorization" : "HCP %s:%s" % (username, password) , "Accept": "application/json"}
        
        url="https://"+self.__host+"/mapi/tenants"
        # get tenants
        try:
            req = urllib2.Request(url, None, headers)
            handler = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            log.error('response code %d' % e.code)
            raise RemoteServerError()
        except urllib2.URLError as e:
            raise Exception("Error accessing URL %s: %s" % (url, e.args))
        else:
            # 200
            content = handler.read()
            tenants = json.loads(content)['name']
            handler.close()
        
        for tenant in tenants:
            start_time=datetime.datetime.fromtimestamp(time.time()-60*self.__query_period).strftime("%Y-%m-%dT%H:%M:00%%2B0930")
            url_tenant="https://"+self.__host+"/mapi/tenants/"+tenant+"/chargebackReport?start="+start_time
            log.debug("querying %s from %s..."% (tenant, start_time))
            try:
                req = urllib2.Request(url_tenant, None, headers)
                handler = urllib2.urlopen(req)
            except urllib2.HTTPError as e:
                log.debug('response code %d' % e.code)
                continue
            except urllib2.URLError as e:
                raise Exception("Error accessing URL %s: %s" % (url, e.args))
            else:
                # 200
                content = handler.read()
                report = json.loads(content)
                data[tenant]=report['chargebackData']
                handler.close()
        return data
