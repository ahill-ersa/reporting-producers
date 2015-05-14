#!/usr/bin/env python

# pylint: disable=broad-except

import threading
from subprocess import Popen, PIPE
import time
import shlex
import uuid
import json
import collections
import requests

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
        pipe = Popen(shlex.split(self.__cmd), stdout=PIPE).stdout
        return ''.join(pipe.readlines()).strip()
    
class FileReader(IDataSource):
    def __init__(self, path):
        self.__path=path
    def get_data(self, **kwargs):
        log.debug("reading file %s"%self.__path)
        with open(self.__path) as f:
            content = ''.join(f.readlines()).strip()
        return content
    
class HTTPReader(IDataSource):
    def __init__(self, url, headers={}, method='GET', verify=False):
        self.__url=url
        self.__headers=headers
        self.__method=method
        self.__verify=verify
    def get_data(self, **kwargs):
        log.debug("accessing URL %s"%self.__url)
        #log.debug("headers %s"%self.__headers)
        response = requests.get(self.__url, headers=self.__headers, verify=self.__verify)
        log.debug('response.text %s' % response.text)
        if response.status_code == 200:
            return response.text
        else:
            log.exception("Error accessing URL %s: %d"%(self.__url, response.status_code))
            response.raise_for_status()

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
            method=self.__config['input'].get('method', 'GET')
            verify=self.__config['input'].get('verify', False)
            self.__input=HTTPReader(url, headers, method, verify)
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
    except SyntaxError, e:
        raise PluginInitialisationError(
            "Plugin %s (%s) contains a syntax error at line %s" %
            (class_name, e.filename, e.lineno))
    except ImportError, e:
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
