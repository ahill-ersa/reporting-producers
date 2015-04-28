#!/usr/bin/env python

# pylint: disable=broad-except

import logging
import sys
import random
import string
import socket
import datetime
import platform

def getLogger(name):
    """Get logging.Logger instance with logger name convention
    """
    if "." in name:
        name = "producer.%s" % name.rpartition(".")[-1]
    return logging.getLogger(name)

def excepthook(exc_type, exc_value, exc_traceback):
    """Except hook used to log unhandled exceptions to log
    """
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    getLogger("producer").critical(
        "Unhandled exception in reporting producer:", exc_info=(exc_type, exc_value, exc_traceback))
    #return sys.__excepthook__(exctype, value, traceback)

def get_log_level(verbose):
    if verbose <= 0:
        return logging.ERROR
    elif verbose == 1:
        return logging.WARNING
    elif verbose == 2:
        return logging.INFO
    return logging.DEBUG

def get_hostname():
    try:
        return socket.getfqdn()
    except:
        return platform.node()
