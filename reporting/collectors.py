#!/usr/bin/env python

# pylint: disable=broad-except

import threading
from subprocess import Popen, PIPE
import time
import shlex
import uuid
import json
import collections
import urllib2, urllib

from reporting.parsers import MatchParser, SplitParser, DummyParser, JsonGrepParser
from reporting.utilities import getLogger, get_hostname
from reporting.exceptions import PluginInitialisationError

log = getLogger(__name__)

class IDataSource(object):
    def get_data(self, **kwargs):
        assert 0, "This method must be defined."

class CommandRunner(IDataSource):
    def __init__(self, cmd):
        self.__cmd=cmd
    def get_data(self, **kwargs):
        log.debug("running cmd %s"%self.__cmd)
        process = Popen(shlex.split(self.__cmd), stdout=PIPE)
        pipe = process.stdout
        output = ''.join(pipe.readlines()).strip()
        process.wait()
        return output
    
class FileReader(IDataSource):
    def __init__(self, path):
        self.__path=path
    def get_data(self, **kwargs):
        log.debug("reading file %s"%self.__path)
        with open(self.__path) as f:
            content = ''.join(f.readlines()).strip()
        return content
    
class HTTPReader(IDataSource):
    def __init__(self, url, headers={}, auth=None):
        self.__url=url
        self.__headers=headers
        self.__auth=auth
    def get_data(self, **kwargs):
        try:
            if self.__auth:
                password_manager = urllib2.HTTPPasswordMgrWithDefaultRealm()
                password_manager.add_password(None, self.__url, self.__auth['username'], self.__auth['password'])
                
                auth = urllib2.HTTPBasicAuthHandler(password_manager) # create an authentication handler
                opener = urllib2.build_opener(auth) # create an opener with the authentication handler
                urllib2.install_opener(opener) # install the opener... 
            
            req = urllib2.Request(self.__url, None, self.__headers)
            handler = urllib2.urlopen(req)
        except urllib2.HTTPError as e:
            log.error('response code %d' % e.code)
            if e.code == 400 or e.code==500:
                raise MessageInvalidError()
            else:
                raise RemoteServerError()
        except urllib2.URLError as e:
            raise Exception("Error accessing URL %s: %s" % (self.__url, e.args))
        else:
            # 200
            response = handler.read()
            log.debug("response %d %s"% (handler.code, response))
            handler.close()
            return response

class Collector(threading.Thread):
    def __init__(self, collector_name, config, output, tailer):
        threading.Thread.__init__(self, name=collector_name)
        self.__collector_name=collector_name
        self.__config=config
        self.__sleep_time=self.__config['input'].get('frequency',10)
        self.__input=None
        self.__parser=None
        self.__output=output
        if self.__config['input']['type']=='command':
            self.__input=CommandRunner(self.__config['input']['source'])
        elif self.__config['input']['type']=='file':
            self.__input=FileReader(self.__config['input']['path'])
        elif self.__config['input']['type']=='http':
            #log.debug('input %s'%self.__config['input'])
            url=self.__config['input']['url']
            headers=self.__config['input'].get('headers', {})
            #log.debug('headers %s'%headers)
            auth=self.__config['input'].get('auth', None)
            self.__input=HTTPReader(url, headers, auth)
        elif self.__config['input']['type']=='class':
            arguments={}
            if 'arguments' in self.__config['input']:
                arguments=self.__config['input']['arguments']
            self.__input=init_object(self.__config['input']['name'], **arguments)
        elif self.__config['input']['type']=='tailer':
            self.__input=tailer
        if 'parser' in self.__config:
            if self.__config['parser']['type']=='match':
                self.__parser=MatchParser(self.__config['parser']['pattern'].strip(), self.__config['parser']['transform'].strip())
            elif self.__config['parser']['type']=='split':
                self.__parser=SplitParser(self.__config['parser']['delimiter'].strip(), self.__config['parser']['transform'].strip())
            elif self.__config['parser']['type']=='dummy':
                self.__parser=DummyParser()
            elif self.__config['parser']['type']=='json':
                arguments={}
                if 'arguments' in self.__config['parser']:
                    arguments=self.__config['parser']['arguments']
                self.__parser=JsonGrepParser(**arguments)
            elif self.__config['parser']['type']=='class':
                arguments={}
                if 'arguments' in self.__config['parser']:
                    arguments=self.__config['parser']['arguments']
                self.__parser=init_object(self.__config['parser']['name'], **arguments)
        self.__running=True
        self.__session_id=str(uuid.uuid4())
        self.__max_error_count=5
        
    def quit(self):
        self.__running=False
        
    def info(self):
        col_info={"name":self.__collector_name, "config":self.__config, "sleep_time": self.__sleep_time}
        col_info["session_id"]=self.__session_id
        return col_info
        
    def run(self):
        count=0
        error_count=0
        log.info("collector %s has started."%self.__collector_name)
        while self.__running:
            args={'config': self.__config['input']}
            if count==self.__sleep_time:
                count=0
                try:
                    data=self.__input.get_data(**args)
                    if isinstance(data, collections.deque) or isinstance(data, list):
                        payload=[]
                        for line in data:
                            log.debug("raw data %s"%line)
                            payload.append(self.generate_payload(line))
                        if len(payload)>0:
                            self.__output.push(payload)
                        else:
                            continue
                    else:
                        log.debug("raw data %s"%data)
                        payload=self.generate_payload(data)
                        self.__output.push(payload)
                except:
                    log.exception('unable to get or parse data.')
                    error_count+=1
                    if error_count>=self.__max_error_count:
                        break
                    if self.__config['input']['type']=='tailer':
                        self.__input.fail(**args)
                else:
                    if self.__config['input']['type']=='tailer':
                        self.__input.success(**args)
            else:
                time.sleep(1)
                count+=1
        self.__output.close()
        log.info("collector %s has stopped."%self.__collector_name)
        
    def generate_payload(self, data):
        if self.__parser:
            data=self.__parser.parse(data)
        log.debug("parsed data %s"%data)
        payload={"id": str(uuid.uuid4()), "session": self.__session_id}
        payload['data']=data
        if 'metadata' in self.__config:
            for m in self.__config['metadata']:
                payload[m]=self.__config['metadata'][m]
        log.debug("payload to push: %s"%payload)
        return payload
        
def init_object(class_name, **arguments):
    mod_name = '.'.join(class_name.split('.')[:-1])
    class_name = class_name.split('.')[-1]
    log.debug("Loading plugin %s %s"%(mod_name, class_name))
    try:
        mod = __import__(mod_name, globals(), locals(), [class_name])
    except SyntaxError as e:
        raise PluginInitialisationError(
            "Plugin %s (%s) contains a syntax error at line %s" %
            (class_name, e.filename, e.lineno))
    except ImportError as e:
        log.exception(e)
        raise PluginInitialisationError(
            "Failed to import plugin %s: %s" %
            (class_name, e[0]))
    klass = getattr(mod, class_name, None)
    if not klass:
        raise PluginInitialisationError(
            'Plugin class %s does not exist' % class_name)
    try:
        return klass(**arguments)
    except Exception as exc:
        raise PluginInitialisationError(
            "Failed to load plugin %s with "
            "the following error: %s - %s" %
            (class_name, exc.__class__.__name__, exc.message))
