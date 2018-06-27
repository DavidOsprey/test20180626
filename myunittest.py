#!/usr/bin/env python
# -*- coding: utf-8 -*-

from myclasses import DictionaryTree, EndpointReader, RangePoller, Summarizer

import mock
import unittest
import requests

class DictionaryTreeTestCase(unittest.TestCase):
    def test_insert_balances_the_tree(self):
        # instantiate the SUT
        sut = DictionaryTree(None, "test")

        test_value1 = {"test":1}
        test_value2 = {"test":2}
        test_value3 = {"test":3}
        
        sut.insert(test_value1)
        sut.insert(test_value2)
        sut.insert(test_value3)
        
        # test that the binary tree root data was set
        self.assertTrue(sut.data != None, "Failed to set dictionary tree root.")

        # test that the binary tree was balanced correctly
        self.assertTrue(sut.highest()["test"] == 3, "Failed to balance dictionary tree for highest value.")
        self.assertTrue(sut.lowest()["test"] == 1, "Failed to balance dictionary tree for lowest value.")


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            return

    if args[0] == 'http://domain.com/camera/1':
        return MockResponse({"camera_id": 1, "images": [{"file_size": 5635}, {"file_size": 8022}, {"file_size": 7632}]}, 200)
    if args[0] == 'http://domain.com/camera/2':
        return MockResponse({"camera_id": 2, "images": [{"file_size": 1565}, {"file_size": 2802}, {"file_size": 18}, {"file_size": 12}]}, 200)
    if args[0] == 'http://domain.com/camera/3':
        return MockResponse({"camera_id": 3, "images": [{"file_size": 235}, {"file_size": 118}, {"file_size": 11231}]}, 200)
    if args[0] == 'http://domain.com/camera/991':
        raise requests.exceptions.ConnectionError()
    if args[0] == 'http://domain.com/camera/992':
        raise requests.exceptions.Timeout()

    return MockResponse(None, 404)

      
class EndpointReaderTestCase(unittest.TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_valid_url_retrieves_data(self, mock_get):
        # instantiate the SUT
        sut = EndpointReader("http://domain.com/camera", 10)
        
        expected = {"camera_id": 1, "images": [{"file_size": 5635}, {"file_size": 8022}, {"file_size": 7632}]}
        json_data = sut.get(1)
        # test that the mocked requests.get was called
        self.assertTrue(mock_get.called, "Failed to call requests.get.")
        # test that we received the expected data
        self.assertEqual(expected, json_data)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_connectionerror_is_handled_gracefully(self, mock_get):
        # instantiate the SUT
        sut = EndpointReader("http://domain.com/camera", 10)
        self.assertRaises(requests.exceptions.ConnectionError, sut.get, 991)

    @mock.patch('requests.get', side_effect=mocked_requests_get)    
    def test_get_timeout_is_handled_gracefully(self, mock_get):
        # instantiate the SUT
        sut = EndpointReader("http://domain.com/camera", 10)
        self.assertRaises(requests.exceptions.Timeout, sut.get, 992)
        

class RangePollerTestCase(unittest.TestCase):
    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_range_poll_retrieves_3_valid_cams(self, mock_get):
        # instantiate the SUT and dependencies
        reader = EndpointReader("http://domain.com/camera", 10)
        sut = RangePoller(reader)

        sut.poll([1,2,3,991,992])
        
        # test that the mocked requests.get was called
        self.assertTrue(mock_get.called, "Failed to call requests.get.")

        # test that we have retrieved json data from the 3 valid cameras
        # while the other 2 that timed out did not affect the process
        self.assertEqual(len(sut.cameras), 3)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_camera_returns_None_upon_ConnectionError_in_get(self, mock_get):
        # instantiate the SUT and dependencies
        reader = EndpointReader("http://domain.com/camera", 10)
        sut = RangePoller(reader)

        # this will generate a ConnectionError exception in the reader
        result = sut.get_camera(991)
        
        # test that the mocked requests.get was called
        self.assertTrue(mock_get.called, "Failed to call requests.get.")

        # test that returned result was None
        self.assertIsNone(result)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_get_camera_returns_None_upon_Timeout_in_get(self, mock_get):
        # instantiate the SUT and dependencies
        reader = EndpointReader("http://domain.com/camera", 10)
        sut = RangePoller(reader)

        # this will generate a Timeout exception in the reader
        result = sut.get_camera(992)
        
        # test that the mocked requests.get was called
        self.assertTrue(mock_get.called, "Failed to call requests.get.")

        # test that returned result was None
        self.assertIsNone(result)

class SummarizerTestCase(unittest.TestCase):
    def test_camera_analyze(self):
        # instantiate the SUT and dependencies
        reader = EndpointReader("http://domain.com/camera", 10)
        poller = RangePoller(reader)
        sut = Summarizer(poller)

        cam_detail = {"camera_id": 2, "images": [{"file_size": 1565}, {"file_size": 2802}, {"file_size": 18}, {"file_size": 12}]}
        result = sut.camera_analyze(cam_detail)

        expected = {'camera_id': 2, 'totalbytes': 4397, 'imagecount': 4, 'largestimage': 2802}
        self.assertEqual(expected, result)

    @mock.patch('requests.get', side_effect=mocked_requests_get)
    def test_compile_results(self, mock_get):
        # instantiate the SUT and dependencies
        reader = EndpointReader("http://domain.com/camera", 10)
        poller = RangePoller(reader)
        sut = Summarizer(poller)

        poller.poll([1,2,3])
        sut.compile()

        self.assertEqual(sut.cams_by_space.data["camera_id"], 1)
        self.assertEqual(sut.cams_by_imagecount.data["camera_id"], 1)
        self.assertEqual(sut.cams_by_largestimage.data["camera_id"], 1)

        self.assertEqual(sut.cams_by_space.lowest()["camera_id"], 2)
        self.assertEqual(sut.cams_by_imagecount.lowest()["camera_id"], 1)
        self.assertEqual(sut.cams_by_largestimage.lowest()["camera_id"], 2)

        self.assertEqual(sut.cams_by_space.highest()["camera_id"], 1)
        self.assertEqual(sut.cams_by_imagecount.highest()["camera_id"], 2)
        self.assertEqual(sut.cams_by_largestimage.highest()["camera_id"], 3)
