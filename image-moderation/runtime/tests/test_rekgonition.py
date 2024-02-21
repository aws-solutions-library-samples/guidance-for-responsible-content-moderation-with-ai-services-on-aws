import os
import boto3
import json

import unittest
from unittest.mock import Mock, MagicMock
from chalicelib.rekognition import RekognitonClient
from chalicelib.exception import InvocationException


class TestRekognitonClient(unittest.TestCase):
    """Depends on sagemaker"""
    def test_detect_labels(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'Labels': [{'Confidence': 77, 'Name': 'Wine'},
                                    {'Confidence': 55, 'Name': 'Smoking'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3)

        detected_labels = client.detect_labels(image_bytes=data, min_confidence=40)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        smoking = detected_labels[0]
        self.assertEqual('Wine', smoking['Label'])
        self.assertEqual('DetectLabels', smoking['ReturnSource'])
        self.assertAlmostEqual(smoking['Confidence'], 77, 3)

        # verify 'wine' label
        wine = detected_labels[1]
        self.assertEqual('Smoking', wine['Label'])
        self.assertEqual('DetectLabels', wine['ReturnSource'])
        self.assertAlmostEqual(wine['Confidence'], 55, 3)

        # verify invocation
        rek_client_boto3.detect_labels.assert_called_once_with(
            Image={
                'Bytes': data,
            },
            MaxLabels=5,
            MinConfidence=40,
            # Features= ["GENERAL_LABELS", "IMAGE_PROPERTIES"],
            Settings={
                'GeneralLabels': {
                    # "LabelCategoryInclusionFilters": ['Flag'],
                    "LabelInclusionFilters": client.label_inclusion_filters
                },
            }
        )

    def test_detect_labels_with_qrcode(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'Labels': [{'Confidence': 77,
                                     'Name': 'QR Code',
                                     'Instances':
                                         [{"BoundingBox": {
                                             "Height": 0.56,
                                             "Left": 0.1,
                                             "Top": 0.3,
                                             "Width": 0.2
                                         }}]},
                                    {'Confidence': 55, 'Name': 'Smoking'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3)

        detected_labels = client.detect_labels(image_bytes=data, min_confidence=40)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        qrcode = detected_labels[0]
        self.assertEqual('QR Code', qrcode['Label'])
        self.assertEqual('DetectLabels', qrcode['ReturnSource'])
        self.assertEqual(qrcode['BoundingBox'], {'Left': 0.1, 'Top': 0.3, 'Height': 0.56, 'Width': 0.2})
        self.assertAlmostEqual(qrcode['Confidence'], 77, 3)

        # verify 'wine' label
        wine = detected_labels[1]
        self.assertEqual('Smoking', wine['Label'])
        self.assertEqual('DetectLabels', wine['ReturnSource'])
        self.assertAlmostEqual(wine['Confidence'], 55, 3)

        # verify invocation
        rek_client_boto3.detect_labels.assert_called_once_with(
            Image={
                'Bytes': data,
            },
            MaxLabels=5,
            MinConfidence=40,
            # Features= ["GENERAL_LABELS", "IMAGE_PROPERTIES"],
            Settings={
                'GeneralLabels': {
                    # "LabelCategoryInclusionFilters": ['Flag'],
                    "LabelInclusionFilters": client.label_inclusion_filters
                },
            }
        )

    def test_detect_labels_with_empty_response(self):
        """
        Unit tests
        """
        # mock boto3 client
        custom_labels = {'Labels': []}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3)

        detected_labels = client.detect_labels(image_bytes=None, bucket='bucket-test', object_name='123',
                                               min_confidence=50, max_labels=9)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 0)

        # verify invocation
        rek_client_boto3.detect_labels.assert_called_once_with(
            Image={
                'S3Object': {
                    'Bucket': 'bucket-test',
                    'Name': '123'
                },
            },
            MaxLabels=9,
            MinConfidence=50,
            # Features= ["GENERAL_LABELS", "IMAGE_PROPERTIES"],
            Settings={
                'GeneralLabels': {
                    # "LabelCategoryInclusionFilters": ['Flag'],
                    "LabelInclusionFilters": client.label_inclusion_filters
                },
            }
        )

    def test_detect_labels_with_exception(self):
        """
        Unit tests
        """
        rek_client_boto3 = Mock()
        rek_client_boto3.detect_labels = MagicMock(side_effect=Exception('Test purpose'))

        client = RekognitonClient(rek_client_boto3)

        with self.assertRaises(InvocationException) as raised_exception:
            client.detect_labels(image_bytes=None, bucket='bucket-test', object_name='123',
                                 min_confidence=50, max_labels=9)

        # verify exception
        self.assertEqual(raised_exception.exception.message, "Test purpose")
        self.assertEqual(raised_exception.exception.error_code, "Exception")

        # verify invocation
        rek_client_boto3.detect_labels.assert_called_once_with(
            Image={
                'S3Object': {
                    'Bucket': 'bucket-test',
                    'Name': '123'
                },
            },
            MaxLabels=9,
            MinConfidence=50,
            # Features= ["GENERAL_LABELS", "IMAGE_PROPERTIES"],
            Settings={
                'GeneralLabels': {
                    # "LabelCategoryInclusionFilters": ['Flag'],
                    "LabelInclusionFilters": client.label_inclusion_filters
                },
            }
        )

    def test_detect_moderation_labels(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'ModerationLabels': [{'Confidence': 77, 'Name': 'Drinking'},
                                              {'Confidence': 88, 'Name': 'ExcludedLabel'},
                                              {'Confidence': 33, 'Name': 'Smoking2'},
                                              {'Confidence': 55, 'Name': 'Smoking'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_moderation_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3, moderation_label_inclusion_filters=['Drinking', 'Smoking2', 'Smoking'])

        detected_labels = client.detect_moderation_labels(image_bytes=data, min_confidence=45, max_labels=2)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        drinking = detected_labels[0]
        self.assertEqual('Drinking', drinking['Label'])
        self.assertEqual('DetectModerationLabels', drinking['ReturnSource'])
        self.assertAlmostEqual(drinking['Confidence'], 77, 3)

        # verify 'wine' label
        smoking = detected_labels[1]
        self.assertEqual('Smoking', smoking['Label'])
        self.assertEqual('DetectModerationLabels', smoking['ReturnSource'])
        self.assertAlmostEqual(smoking['Confidence'], 55, 3)

        # verify invocation
        rek_client_boto3.detect_moderation_labels.assert_called_once_with(
            Image={
                'Bytes': data,
            },
            MinConfidence=45
        )

    def test_detect_moderation_labels_without_filtering(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'ModerationLabels': [{'Confidence': 77, 'Name': 'Drinking'},
                                              {'Confidence': 33, 'Name': 'Smoking2'},
                                              {'Confidence': 55, 'Name': 'Smoking'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_moderation_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3, enable_moderation_filter=False)

        detected_labels = client.detect_moderation_labels(image_bytes=data, min_confidence=45, max_labels=2)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        drinking = detected_labels[0]
        self.assertEqual('Drinking', drinking['Label'])
        self.assertEqual('DetectModerationLabels', drinking['ReturnSource'])
        self.assertAlmostEqual(drinking['Confidence'], 77, 3)

        # verify 'wine' label
        smoking = detected_labels[1]
        self.assertEqual('Smoking', smoking['Label'])
        self.assertEqual('DetectModerationLabels', smoking['ReturnSource'])
        self.assertAlmostEqual(smoking['Confidence'], 55, 3)

        # verify invocation
        rek_client_boto3.detect_moderation_labels.assert_called_once_with(
            Image={
                'Bytes': data,
            },
            MinConfidence=45
        )

    def test_detect_moderation_labels_with_empty_response(self):
        """
        Unit tests
        """
        # mock boto3 client
        custom_labels = {'ModerationLabels': [{'Confidence': 77, 'Name': 'Drinking'},
                                              {'Confidence': 33, 'Name': 'Smoking2'},
                                              {'Confidence': 55, 'Name': 'Smoking'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.detect_moderation_labels = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3)

        detected_labels = client.detect_moderation_labels(image_bytes=None, bucket='b1', object_name='o1',
                                                          min_confidence=45, max_labels=2)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 0)

        # verify invocation
        rek_client_boto3.detect_moderation_labels.assert_called_once_with(
            Image={
                'S3Object': {
                    'Bucket': 'b1',
                    'Name': 'o1'
                },
            },
            MinConfidence=45
        )

    def test_detect_moderation_labels_with_exception(self):
        """
        Unit tests
        """
        rek_client_boto3 = Mock()
        rek_client_boto3.detect_moderation_labels = MagicMock(side_effect=Exception('Test moderation ex'))

        client = RekognitonClient(rek_client_boto3)

        with self.assertRaises(InvocationException) as raised_exception:
            client.detect_moderation_labels(image_bytes=None,
                                            bucket='b1',
                                            object_name='o1',
                                            min_confidence=45,
                                            max_labels=2)

        # verify exception
        self.assertEqual(raised_exception.exception.message, "Test moderation ex")
        self.assertEqual(raised_exception.exception.error_code, "Exception")

        # verify invocation
        rek_client_boto3.detect_moderation_labels.assert_called_once_with(
            Image={
                'S3Object': {
                    'Bucket': 'b1',
                    'Name': 'o1'
                },
            },
            MinConfidence=45
        )

    def test_search_face(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'FaceMatches': [{'Similarity': 97, 'Face': {'ExternalImageId': 'face1'}},
                                         {'Similarity': 95, 'Face': {'ExternalImageId': 'face2'}}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.search_faces_by_image = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3, collection_id='collection_name')

        detected_labels = client.search_faces_by_image(image_bytes=data, face_match_threshold=90, max_faces=2)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 2)

        # verify 'smoking' label
        face1 = detected_labels[0]
        self.assertEqual('face1', face1['Label'])
        self.assertEqual('FaceSearch', face1['ReturnSource'])
        self.assertAlmostEqual(face1['Confidence'], 97, 3)

        # verify 'wine' label
        face2 = detected_labels[1]
        self.assertEqual('face2', face2['Label'])
        self.assertEqual('FaceSearch', face2['ReturnSource'])
        self.assertAlmostEqual(face2['Confidence'], 95, 3)

        # verify invocation
        rek_client_boto3.search_faces_by_image.assert_called_once_with(
            CollectionId='collection_name',
            FaceMatchThreshold=90,
            Image={
                'Bytes': data,
            },
            MaxFaces=2
        )

    def test_search_faces_with_empty_response(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'FaceMatches': []}

        rek_client_boto3 = Mock()
        rek_client_boto3.search_faces_by_image = MagicMock(return_value=custom_labels)

        client = RekognitonClient(rek_client_boto3, customer_facial_threshold=40, collection_id='collection_name')

        detected_labels = client.search_faces_by_image(image_bytes=data, face_match_threshold=45, max_faces=2)

        # verify results
        self.assertGreaterEqual(len(detected_labels), 0)

        # verify invocation
        rek_client_boto3.search_faces_by_image.assert_called_once_with(
            CollectionId='collection_name',
            FaceMatchThreshold=45,
            Image={
                'Bytes': data,
            },
            MaxFaces=2
        )

    def test_search_faces_by_image_with_exception(self):
        """
        Unit tests
        """
        rek_client_boto3 = Mock()
        rek_client_boto3.search_faces_by_image = MagicMock(side_effect=Exception('Test moderation ex'))

        client = RekognitonClient(rek_client_boto3, customer_facial_threshold=45, collection_id='collection_name')

        with self.assertRaises(InvocationException) as raised_exception:
            client.search_faces_by_image(image_bytes=None, bucket='b1', object_name='o2', face_match_threshold=45,
                                         max_faces=2)

        # verify exception
        self.assertEqual(raised_exception.exception.message, "Test moderation ex")
        self.assertEqual(raised_exception.exception.error_code, "Exception")

        # verify invocation
        rek_client_boto3.search_faces_by_image.assert_called_once_with(
            CollectionId='collection_name',
            FaceMatchThreshold=45,
            Image={
                'S3Object': {
                    'Bucket': 'b1',
                    'Name': 'o2'
                },
            },
            MaxFaces=2
        )

    def test_search_celebrities(self):
        """
        Unit tests
        """
        data = bytearray([1, 2, 3])

        # mock boto3 client
        custom_labels = {'CelebrityFaces': [{'MatchConfidence': 72, 'Name': 'face1', 'Id': 'id_1'},
                                            {'MatchConfidence': 87, 'Name': 'face1', 'Id': 'id_1'},
                                            {'MatchConfidence': 66, 'Name': 'face2', 'Id': 'id_2'},
                                            {'MatchConfidence': 44, 'Name': 'face3', 'Id': 'id_3'}]}

        rek_client_boto3 = Mock()
        rek_client_boto3.recognize_celebrities = MagicMock(return_value=custom_labels)

        client: RekognitonClient = RekognitonClient(rek_client_boto3, celebrity_facial_threshold=40)

        detected_labels = client.search_celebrities_by_image(image_bytes=data, face_match_threshold=45, max_faces=2)

        # verify results
        self.assertEqual(len(detected_labels), 2)

        # verify 'smoking' label
        face1 = detected_labels[0]
        self.assertEqual('face1', face1['Label'])
        self.assertEqual('CelebritySearch', face1['ReturnSource'])
        self.assertAlmostEqual(face1['Confidence'], 87, 3)

        # verify 'wine' label
        face2 = detected_labels[1]
        self.assertEqual('face2', face2['Label'])
        self.assertEqual('CelebritySearch', face2['ReturnSource'])
        self.assertAlmostEqual(face2['Confidence'], 66, 3)

        # verify invocation
        rek_client_boto3.recognize_celebrities.assert_called_once_with(
            Image={
                'Bytes': data,
            }
        )
