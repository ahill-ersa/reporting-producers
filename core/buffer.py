#!/usr/bin/env python

"""Dump each line of data from stdin into a staging file, ready for upload."""

import logging

import yaml

import reporting

config = yaml.load(open("config.yaml", "r"))

reporting.Buffer(directory=config["directory"], log_level=logging.INFO).execute()
