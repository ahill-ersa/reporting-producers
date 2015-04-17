#!/usr/bin/env python

# pylint: disable=broad-except

import re

from reporting.utilities import getLogger

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
        return self.__transform.format(*match_groups)
    
class SplitParser(IParser):
    def __init__(self, delimiter, transform):
        self.__delimiter=delimiter
        self.__transform=transform
    def parse(self, data):
        log.debug("delimiter %s" % self.__delimiter)
        list = re.split(self.__delimiter, data)
        return self.__transform.format(*list)