#!/usr/bin/env python

"""Push staged data to the reporting API. Loops indefinitely."""

import logging

import yaml

import reporting

config = yaml.load(open("config.yaml", "r"))

client = reporting.Reporting(config["connection"], log_level=logging.INFO)

reporting.Pusher(client=client, directory=config["directory"], log_level=logging.INFO).execute()
