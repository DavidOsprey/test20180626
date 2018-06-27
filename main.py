#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
import sys
import argparse
from random import randint

from myclasses import DictionaryTree, EndpointReader, RangePoller, Summarizer

def int_csv(string):
    intlist = []
    parsed = string.split(',')
    for entry in parsed:
        intlist.append(int(entry))
    if len(intlist) <= 0:
        msg = "%r is not an integer csv list" % string
        raise argparse.ArgumentTypeError(msg)
    return intlist

def poll_and_summarize():
    args = parser.parse_args()

    """ json format: {"camera_id": 10, "images": [{"file_size": 5635}, {"file_size": 8022}, {"file_size": 7632}]} """
    """ reading tested with "http://www.mocky.io/v2/5b32d8103400002e343fd4fa """
    reader = EndpointReader("http://domain.com/camera", args.timeout)

    """ by default, the real requests.get is being called """
    """ http get calls can be replaced with a fake (random json values in struct) for internal testing """
    if args.simulate:
        reader.enable_fake_get()
    
    poller = RangePoller(reader)
    poller.poll(args.cameras)

    summarizer = Summarizer(poller)
    summarizer.compile()
    summarizer.print_stats()


parser = argparse.ArgumentParser(description='Poll and analyze camera information.')
parser.add_argument('--timeout', dest='timeout', metavar='T', type=int, default=10, 
                    help='timeout value for reading data from REST endpoints')
parser.add_argument('--cameras', dest='cameras', metavar='INT_CSV', type=int_csv, required=True,
                    help='comma separated integer list of camera IDs to poll')
parser.add_argument('--simulate', dest='simulate', metavar='S', type=bool, default=False,
                    help='use simulated requests.get results for testing')


poll_and_summarize()

