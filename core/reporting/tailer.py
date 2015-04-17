#!/usr/bin/env python

# pylint: disable=broad-except

from reporting.collections import IDataSource

class Tailer(IDataSource):
    def __init__(self, target):
        self.__target=target
        
    