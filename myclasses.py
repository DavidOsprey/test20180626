#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
import json
from random import randint
import sys

class DictionaryTree(object):
    """Class for storing dictionaries in a binary tree"""
    """having one of the dictionary keys as sort criteria"""
    def __init__(self, data, criteria):
        self.left = None
        self.right = None
        self.data = data
        self.criteria = criteria

    def insert(self, data):
        if self.data:
            if data[self.criteria] < self.data[self.criteria]:
                if self.left is None:
                    self.left = DictionaryTree(data, self.criteria)
                else:
                    self.left.insert(data)
            elif data[self.criteria] > self.data[self.criteria]:
                if self.right is None:
                    self.right = DictionaryTree(data, self.criteria)
                else:
                    self.right.insert(data)
        else:
            self.data = data

    def highest(self):
        value = self
        while value.right:
            value = value.right
        return value.data

    def lowest(self):
        value = self
        while value.left:
            value = value.left
        return value.data



class EndpointReader(object):
    """Class for reading camera data from a REST EndpointReader."""
    def __init__(self, base_url, timeout_val):
        self.base_url = base_url
        self.timeout_val = timeout_val
        self.disable_fake_get()

    def enable_fake_get(self):
        self.fake_get = True

    def disable_fake_get(self):
        self.fake_get = False

    def random_data(self, camera_id):
        obj = {"camera_id":int(camera_id),"images":[]}
        for i in range(1, randint(1, 20)):
            obj["images"].append({"file_size":randint(5, 9999)})
        return json.dumps(obj)

    def get(self, camera_id):
        end_url = "%s/%s" % (self.base_url, camera_id)
        if self.fake_get:
            json_data = json.loads(self.random_data(camera_id))
        else:
            response = requests.get(end_url, verify=False, timeout=self.timeout_val)
            response.raise_for_status()
            json_data = response.json()

        #print('Received: ' + format(json_data))
        return json_data



class RangePoller(object):
    """Service for polling data from multiple cameras"""

    def __init__(self, reader):
        self.reader = reader
        self.clear()

    def clear(self):
        self.cameras = {}
                
    def get_camera(self, camera_id):
        try:
            return self.reader.get(camera_id)
        except (requests.exceptions.Timeout,
                requests.exceptions.ConnectionError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ReadTimeout) as e:
            #print('Camera ' + format(camera_id) + ' timed out!')
            return None
        except requests.exceptions.RequestException as e:
            print("FATAL ERROR: " + format(e))
            sys.exit(1)
            
    def poll(self, camera_list):
        self.clear()
        for camera_id in camera_list:
            cam_detail = self.get_camera(camera_id)
            if cam_detail != None:
                self.cameras.update({camera_id : cam_detail})



class Summarizer(object):
    """Service for analyzing and summarizing data from a poll"""

    def __init__(self, poller):
        self.poller = poller
        self.clear()

    def clear(self):
        self.cams_by_space = DictionaryTree(None, "totalbytes")
        self.cams_by_imagecount = DictionaryTree(None, "imagecount")
        self.cams_by_largestimage = DictionaryTree(None, "largestimage")

    def camera_analyze(self, cam_detail):
        cam_stats = {
            "camera_id":cam_detail["camera_id"],
            "totalbytes":0,
            "imagecount":len(cam_detail["images"]),
            "largestimage":0
        }
        for img in cam_detail["images"]:
            img_size = int(img["file_size"])
            cam_stats["totalbytes"] = cam_stats["totalbytes"] + img_size
            if cam_stats["largestimage"] < img_size:
                cam_stats["largestimage"] = img_size
        return cam_stats
                
    def compile(self):
        self.clear()
        for camera_detail in self.poller.cameras.values():
            cam_stats = self.camera_analyze(camera_detail)
            #print("  stats: " + format(cam_stats))
            self.cams_by_space.insert(cam_stats)
            self.cams_by_imagecount.insert(cam_stats)
            self.cams_by_largestimage.insert(cam_stats)

    def print_stats(self):
        print("Summary:")
        print("  Cam with most space used: " + format(self.cams_by_space.highest()))
        print("  Cam with most images    : " + format(self.cams_by_imagecount.highest()))
        print("  Cam with largest image  : " + format(self.cams_by_largestimage.highest()))
        print()
