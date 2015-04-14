#!/usr/bin/env python

# pylint: disable=broad-except

import logging
import sys
import random
import string
import socket
import datetime

def getLogger(name):
    """Get logging.Logger instance with logger name convention
    """
    if "." in name:
        name = "producer.%s" % name.rpartition(".")[-1]
    return logging.getLogger(name)

def excepthook(exctype, value, traceback):
    """Except hook used to log unhandled exceptions to log
    """
    getLogger("producer").critical(
        "Unhandled exception in reporting producer:", exc_info=True)
    return sys.__excepthook__(exctype, value, traceback)

def get_log_level(verbose):
    if verbose <= 0:
        return logging.ERROR
    elif verbose == 1:
        return logging.WARNING
    elif verbose == 2:
        return logging.INFO
    return logging.DEBUG
