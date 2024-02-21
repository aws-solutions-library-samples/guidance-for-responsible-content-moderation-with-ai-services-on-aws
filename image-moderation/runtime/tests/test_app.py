import os
import json
import ast
from datetime import datetime

import app
from chalicelib.exception import InvocationException

from unittest import TestCase
from unittest.mock import Mock, MagicMock
from pytest import fixture
from chalice.test import Client


@fixture
def api_client():
    with Client(app.app, stage_name='dev') as client:
        yield client


@fixture(autouse=True)
def _get_mock_api_client(request, api_client):
    request.cls._api_client = api_client


class TestDetectLabels(TestCase):
    def test_detect_labels_with_error_url(self):
        url = 'www.test.com'

        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Url': url
                }
            })
        )

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body,
                         {'Code': 'BadRequestError', 'Message': "{'Image': {'Url': ['Not a valid URL.']}}"})

    def test_detect_labels_with_vague_image_info(self):
        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Object': {
                        'Bucket': 'bucket',
                        'Name': 'object key'
                    },
                    'Url': "http://www.test.image"
                },
                'ReturnSource': ["DetectModerationLabels", "FaceSearch", "DetectLabels", "DetectByCustomModels"],
                'MinConfidence': 30,
                'MaxLabels': 30
            })
        )

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body['Code'], 'BadRequestError')
        self.assertEqual(response.json_body['Message'],
                         "{'Image': {'_schema': ['Cannot have Url and Object both at the sametime in Image.']}}")

    def test_detect_labels_with_incorrect_max_labels(self):
        url = 'www.test.com'

        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Object': {
                        'Bucket': 'bucket',
                        'Name': 'object key'
                    }
                },
                'ReturnSource': ["DetectModerationLabels", "FaceSearch", "DetectLabels", "DetectByCustomModels"],
                'MinConfidence': 30,
                'MaxLabels': 4097
            })
        )

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body['Code'], 'BadRequestError')
        self.assertEqual(response.json_body['Message'], "{'MaxLabels': ['Invalid value.']}")

    def test_detect_labels_with_incorrect_min_confidence(self):
        url = 'www.test.com'

        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Object': {
                        'Bucket': 'bucket',
                        'Name': 'object key'
                    }
                },
                'ReturnSource': ["DetectModerationLabels", "FaceSearch", "DetectLabels", "DetectByCustomModels"],
                'MinConfidence': 101,
                'MaxLabels': 4096
            })
        )

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body['Code'], 'BadRequestError')
        self.assertEqual(response.json_body['Message'], "{'MinConfidence': ['Invalid value.']}")

    def test_detect_labels_without_image(self):
        url = 'www.test.com'

        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'MinConfidence': 30,
                'ReturnSource': ["DetectModerationLabels", "FaceSearch"]
            })
        )

        # assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body['Code'], 'BadRequestError')
        self.assertEqual(response.json_body['Message'], "{'Image': ['Missing data for required field.']}")

    def test_detect_labels_with_incorrect_return_source(self):
        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Object': {
                        'Bucket': 'bucket',
                        'Name': 'object key'
                    }
                },
                'ReturnSource': ["Incorrect_DetectModerationLabels", "FaceSearch"],
                'MinConfidence': 30
            })
        )

        # assert Return resource {return_resource} not one of {_RETURN_RESOURCES}
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json_body['Code'], 'BadRequestError')
        self.assertEqual(response.json_body['Message'],
                         "{'ReturnSource': [\"Return resource Incorrect_DetectModerationLabels not one of ['DetectLabels', 'DetectModerationLabels', 'FaceSearch', 'CelebritySearch', 'DetectByCustomModels']\"]}")

    def test_detect_labels_with_no_bytes_downloaded(self):
        url = 'https://www.test.com'

        # mock image handler
        app.get_image_handler = Mock()
        app.get_image_handler().image_handler = MagicMock(return_value=([], "hashed image data"))

        # request server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Url': url
                }
            })
        )

        # assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json_body['Labels'], [])

        # assert image handler
        app.get_image_handler().image_handler.assert_called_once
        app.get_image_handler().image_handler.assert_called_with(url, bucket=None, object_name=None)

    def test_detect_labels_with_download_and_detection(self):
        url = 'https://www.test.com'
        image_data = [bytes('1' * 8, 'ascii')]
        labels = [
            {
                "Label": "terrisom",
                "ReturnSource": "DetectLabels",
                "Confidence": 88.88},
            {
                "Label": "Chinese-flag",
                "ReturnSource": "DetectModerationLabels",
                "Confidence": 18.99,
                "Words": ["QQ", "1234567890"]
            }]

        # mock image handler
        app.get_image_handler = Mock()
        app.get_image_handler().image_handler = MagicMock(return_value=[image_data, "tested_hash_image_data"])
        # mock labels handler
        app.get_detect_labels_handler = Mock()
        app.get_detect_labels_handler().detect_image_labels = MagicMock(return_value=labels)

        ## invoke server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Url': url
                },
                'ReturnSource': ['DetectByCustomModels'],
                'MinConfidence': 30
            })
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json_body['Labels']), 2)
        self.assertEqual(response.json_body['Labels'], labels)

        # assert image handler
        app.get_image_handler().image_handler.assert_called_once
        app.get_image_handler().image_handler.assert_called_with(url, bucket=None, object_name=None)

        # assert detection handler
        app.get_detect_labels_handler().detect_image_labels.assert_called_once
        app.get_detect_labels_handler().detect_image_labels.assert_called_with(
            return_sources=['DetectByCustomModels'],
            images=image_data,
            min_confidence=30,
            max_labels=50,
            url_hint=url)

    def test_detect_labels_with_backend_exceptions(self):
        url = 'https://www.test.com'
        image_data = [bytes('1' * 8, 'ascii')]
        labels = [
            {
                "Label": "terrisom",
                "ReturnSource": "DetectLabels",
                "Confidence": 88.88},
            {
                "Label": "Chinese-flag",
                "ReturnSource": "DetectModerationLabels",
                "Confidence": 18.99,
                "Words": ["QQ", "1234567890"]
            }]

        # mock image handler
        app.get_image_handler = Mock()
        app.get_image_handler().image_handler = MagicMock(return_value=[image_data, "tested_hash_image_data"])
        # mock labels handler
        app.get_detect_labels_handler = Mock()
        app.get_detect_labels_handler().detect_image_labels = MagicMock(
            side_effect=InvocationException.backend_exceptions(exceptions=[('op1', Exception('ex_op1')), ('op2', Exception('ex_op2'))]))


        ## invoke server
        response = self._api_client.http.post(
            '/Moderation/DetectImageLabels',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                'Image': {
                    'Url': url
                },
                'ReturnSource': ['DetectByCustomModels'],
                'MinConfidence': 30
            })
        )

        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.json_body['Code'], 'TooManyRequestsError')
        self.assertEqual(response.json_body['Message'], '[op1 has errors: ex_op1, op2 has errors: ex_op2]')

        # assert image handler
        app.get_image_handler().image_handler.assert_called_once
        app.get_image_handler().image_handler.assert_called_with(url, bucket=None, object_name=None)

        # assert detection handler
        app.get_detect_labels_handler().detect_image_labels.assert_called_once
        app.get_detect_labels_handler().detect_image_labels.assert_called_with(
            return_sources=['DetectByCustomModels'],
            images=image_data,
            min_confidence=30,
            max_labels=50,
            url_hint=url)

    
