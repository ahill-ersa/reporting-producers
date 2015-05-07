#!/usr/bin/env python

# pylint: disable=broad-except

import re
import json
import time

from reporting.utilities import getLogger, get_hostname

log = getLogger(__name__)

class IParser(object):
    def parse(self):
        assert 0, "This method must be defined."

class MatchParser(IParser):
    def __init__(self, pattern, transform):
        self.__pattern=pattern
        self.__transform=transform
    def parse(self, data):
        log.debug("match %s" % self.__pattern)
        match_obj = re.match(self.__pattern, data, re.M|re.I)
        match_groups = match_obj.groups()
        result = self.__transform.format(*match_groups)
        output = json.loads(result)
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output
    
class SplitParser(IParser):
    def __init__(self, delimiter, transform):
        self.__delimiter=delimiter
        self.__transform=transform
    def parse(self, data):
        log.debug("delimiter %s" % self.__delimiter)
        list = re.split(self.__delimiter, data)
        result = self.__transform.format(*list)
        log.debug("result %s"%result)
        output = json.loads(result)
        log.debug("output %s"%output)
        output['timestamp'] = int(time.time())
        output['hostname'] = get_hostname()
        return output
    