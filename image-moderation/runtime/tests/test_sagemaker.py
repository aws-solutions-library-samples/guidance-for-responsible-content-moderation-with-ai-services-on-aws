import os
import boto3
import json

import unittest
from unittest.mock import Mock, MagicMock

from chalicelib.sagemaker import SageMakerClient
from chalicelib.exception import InvocationException


@unittest.skipUnless(os.environ.get('RUN_INTEG_TESTS', False),
                     "Skipping integ tests as environment value (RUN_INTEG_TESTS) is not True.")
class TestSageMakerClientIntegrationTest(unittest.TestCase):
    """
    Depends on sagemaker installed, and please change enpoint name(endpoint_name) for the test in setUp()
    """

    def setUp(self):
        endpoint_name = 'ImageModerationSageMakerCustomLabelEndpointA87418F-7EUPo1MAjG3d'

        client = boto3.Session().client('sagemaker-runtime')
        self._sagemaker_client = SageMakerClient(client, endpoint_name)

    def test_detect_labels(self):
        """
        make sure the working dir is {project_root}/code/image-moderation
        """
        with open('tests/resources/flag_two.jpg', "rb") as image:
            data = image.read()

        labels = self._sagemaker_client.detect_labels(image_bytes=data)

        # verify results
        self.assertGreaterEqual(len(labels), 1)

        # verify 'Suggestive' label
        label = next(filter(lambda label: label['Label'] == '中国国旗', labels), None)

        self.assertEqual('中国国旗', label['Label'])
        self.assertEqual('DetectByCustomModels', label['ReturnSource'])
        self.assertEqual('pass', label['Suggestion'])
        self.assertGreater(label['Confidence'], 60)


class TestSageMakerClient(unittest.TestCase):
    """Depends on sagemaker"""

    def test_detect_labels(self):
        """
        Unit tests
        """
        endpoint_name = "enpoint-sage"
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'CustomLabels': [{'Confidence': 0.55, 'Label': 'Smoking'},
                                          {'Confidence': 0.77, 'Label': 'Wine'},
                                          {'Confidence': 0.33, 'Label': 'not_included'}]}

        response = {}
        response['Body'] = Mock()
        response['Body'].read = MagicMock(return_value=json.dumps(custom_labels))
        sagemaker_client_boto3 = Mock()
        sagemaker_client_boto3.invoke_endpoint = MagicMock(return_value=response)

        client = SageMakerClient(sagemaker_client_boto3, endpoint_name)

        detected_labels = client.detect_labels(image_bytes=data, min_confidence=40)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        smoking = detected_labels[0]
        self.assertEqual('Wine', smoking['Label'])
        self.assertEqual('DetectByCustomModels', smoking['ReturnSource'])
        self.assertEqual('pass', smoking['Suggestion'])
        self.assertAlmostEqual(smoking['Confidence'], 77, 3)

        # verify 'wine' label
        wine = detected_labels[1]
        self.assertEqual('Smoking', wine['Label'])
        self.assertEqual('DetectByCustomModels', wine['ReturnSource'])
        self.assertEqual('pass', wine['Suggestion'])
        self.assertAlmostEqual(wine['Confidence'], 55, 3)

        # verify invocation
        sagemaker_client_boto3.invoke_endpoint.assert_called_once_with(
            EndpointName=endpoint_name,
            ContentType='application/x-image',
            Body=data,
            Accept='application/json'
        )

    def test_detect_labels_with_empty_response(self):
        """
        Unit tests
        """
        endpoint_name = "enpoint-sage"
        data = bytearray([1, 8, 6])

        # mock boto3 client
        custom_labels = {'CustomLabels': []}

        response = {}
        response['Body'] = Mock()
        response['Body'].read = MagicMock(return_value=json.dumps(custom_labels))
        sagemaker_client_boto3 = Mock()
        sagemaker_client_boto3.invoke_endpoint = MagicMock(return_value=response)

        client = SageMakerClient(sagemaker_client_boto3, endpoint_name)

        detected_labels = client.detect_labels(image_bytes=data, min_confidence=40)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 0)

        # verify invocation
        sagemaker_client_boto3.invoke_endpoint.assert_called_once_with(
            EndpointName=endpoint_name,
            ContentType='application/x-image',
            Body=data,
            Accept='application/json'
        )

    def test_detect_labels_with_exception(self):
        """
        Unit tests
        """
        endpoint_name = "enpoint-sage"
        data = bytearray([1, 8, 6])

        # mock boto3 client
        custom_labels = {'CustomLabels': []}

        response = {}
        response['Body'] = Mock()
        response['Body'].read = MagicMock(return_value=json.dumps(custom_labels))
        sagemaker_client_boto3 = Mock()
        sagemaker_client_boto3.invoke_endpoint = MagicMock(side_effect=Exception('Test purpose'))

        client = SageMakerClient(sagemaker_client_boto3, endpoint_name)

        with self.assertRaises(InvocationException) as raised_exception:
            response = client.detect_labels(image_bytes=data, min_confidence=40)

        # verify results
        self.assertEqual('Test purpose', raised_exception.exception.message)
        self.assertEqual('Exception', raised_exception.exception.error_code)
        self.assertEqual('Sagemaker_' + endpoint_name, raised_exception.exception.operation_name)

        # verify invocation
        sagemaker_client_boto3.invoke_endpoint.assert_called_once_with(
            EndpointName=endpoint_name,
            ContentType='application/x-image',
            Body=data,
            Accept='application/json'
        )
