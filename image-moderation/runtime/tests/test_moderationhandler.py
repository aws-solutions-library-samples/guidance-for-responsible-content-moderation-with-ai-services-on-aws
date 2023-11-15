from unittest import TestCase
from unittest.mock import Mock, MagicMock, call

from chalicelib.moderationhandler import ModerationHandler
from chalicelib.exception import InvocationException


class TestDetectLabelsAPI(TestCase):
    def test_detect_image_labels_with_errors_repeat(self):
        self.test_detect_image_labels_with_errors()
        for i in range(1000):
            self.test_detect_image_labels_with_errors()

    def test_detect_image_labels_with_errors(self):
        image_list = [bytearray([1, 2, 3])]

        # rek_client
        rek_client = Mock()
        rek_client.detect_labels = MagicMock(
            side_effect=[InvocationException.from_client_exception(InvocationException('detect_labels', '01', 'msg'),'detect_labels')])
        rek_client.detect_moderation_labels = MagicMock(
            side_effect=[InvocationException.from_client_exception(InvocationException('detect_moderation_labels'),'detect_moderation_labels')])
        rek_client.search_faces_by_image = MagicMock(
            side_effect=[InvocationException.from_client_exception(InvocationException('search_faces_by_image'),'search_faces_by_image')])
        rek_client.search_celebrities_by_image = MagicMock(
            side_effect=[InvocationException.from_client_exception(InvocationException('search_celebrities_by_image'),'search_celebrities_by_image')])

        # sagemaker_client
        sagemaker_client = Mock()
        sagemaker_client.detect_labels = MagicMock(
            side_effect=[InvocationException.from_client_exception(InvocationException('Test'),'sage_detect_labels')])

        # handler
        handler = ModerationHandler(rek_client=rek_client,
                                    sagemaker_client=sagemaker_client)

        # invoke
        with self.assertRaises(InvocationException) as raised_exception:
            results = handler.detect_image_labels(images=image_list,
                                                  return_sources=["DetectLabels", "DetectModerationLabels",
                                                                  "FaceSearch", "DetectByCustomModels","CelebritySearch"],
                                                  min_confidence=1,
                                                  max_labels=4)

        # verify results
        self.assertEqual(raised_exception.exception.error_code, 'backend_errors')
        self.assertEqual(raised_exception.exception.operation_name, 'detect_image_labels')
        self.assertTrue('DetectLabels has errors: ' in raised_exception.exception.message)
        self.assertTrue('DetectModerationLabels has errors: ' in raised_exception.exception.message)
        self.assertTrue('FaceSearch has errors: ' in raised_exception.exception.message)
        self.assertTrue('CelebritySearch has errors: ' in raised_exception.exception.message)
        self.assertTrue('DetectByCustomModels has errors: ' in raised_exception.exception.message)

        # verify detect labels
        self.assertEqual(rek_client.detect_labels.call_count, 1)
        detect_labels_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, min_confidence=1, max_labels=4)]
        rek_client.detect_labels.assert_has_calls(any_order=True,
                                                  calls=detect_labels_calls)

        # verify detect moderation labels
        self.assertEqual(rek_client.detect_moderation_labels.call_count, 1)
        detect_moderation_labels_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, min_confidence=1, max_labels=4)]
        rek_client.detect_moderation_labels.assert_has_calls(any_order=True,
                                                             calls=detect_moderation_labels_calls)

        # verify search faces
        self.assertEqual(rek_client.search_faces_by_image.call_count, 1)
        search_faces_by_image_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, face_match_threshold=1, max_faces=4)]
        rek_client.search_faces_by_image.assert_has_calls(any_order=True,
                                                          calls=search_faces_by_image_calls)

        # verify search celebrity
        self.assertEqual(rek_client.search_celebrities_by_image.call_count, 1)
        search_celebrities_by_image_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, face_match_threshold=1, max_faces=4)]
        rek_client.search_faces_by_image.assert_has_calls(any_order=True,
                                                          calls=search_celebrities_by_image_calls)

        # verify sagemaker
        sagemaker_detect_labels_calls = [
            call(image_bytes=image_list[0], min_confidence=1)]
        self.assertEqual(sagemaker_client.detect_labels.call_count, 1)
        sagemaker_client.detect_labels.assert_has_calls(calls=sagemaker_detect_labels_calls)


    def test_detect_image_labels_with_one_item(self):
        image_list = [bytearray([1, 2, 3])]

        # prepare data
        res_detect_labels = [{'Label': 'a', 'Confidence': 30},
                             {'Label': 'b', 'Confidence': 40},
                             {'Label': 'c', 'Confidence': 55}]
        res_detect_moderation_labels = [
            {'Label': 'a', 'Confidence': 98},
            {'Label': 'd', 'Confidence': 88},
            {'Label': 'e', 'Confidence': 33}]
        res_search_faces_by_image = [
            {'Label': 'f', 'Confidence': 22},
            {'Label': 'g', 'Confidence': 11},
            {'Label': 'c', 'Confidence': 20}]

        res_sagemaker_detect_labels = [
            {'Label': 'h', 'Confidence': 100},
            {'Label': 'i', 'Confidence': 77}]

        res_search_celebrities_by_image = [
            {'Label': 'k', 'Confidence': 99.1},
            {'Label': 'l', 'Confidence': 68.1}]

        res_orc_reg = [
            {'Label': 'm', 'Confidence': 89.1},
            {'Label': 'n', 'Confidence': 70.1}]

        rek_client = Mock()
        rek_client.detect_labels = MagicMock(return_value=res_detect_labels)
        rek_client.detect_moderation_labels = MagicMock(return_value=res_detect_moderation_labels)
        rek_client.search_faces_by_image = MagicMock(return_value=res_search_faces_by_image)
        rek_client.search_celebrities_by_image = MagicMock(return_value=res_search_celebrities_by_image)

        sagemaker_client = Mock()
        sagemaker_client.detect_labels = MagicMock(return_value=res_sagemaker_detect_labels)

        # handler
        handler = ModerationHandler(rek_client=rek_client, sagemaker_client=sagemaker_client)

        # invoke
        results = handler.detect_image_labels(images=image_list,
                                              return_sources=["DetectLabels", "DetectModerationLabels",
                                                              "FaceSearch", "DetectByCustomModels",
                                                              "CelebritySearch"],
                                              min_confidence=1,
                                              max_labels=4)

        # verify results
        self.assertEqual(4, len(results))
        # verify label h
        self.assertEqual('h', results[0]['Label'])
        self.assertAlmostEqual(100, results[0]['Confidence'], places=3)
        # verify label k
        self.assertEqual('k', results[1]['Label'])
        self.assertAlmostEqual(99.1, results[1]['Confidence'], places=3)
        # verify label a
        self.assertEqual('a', results[2]['Label'])
        self.assertAlmostEqual(98, results[2]['Confidence'], places=3)
        # verify label m
        self.assertEqual('m', results[3]['Label'])
        self.assertAlmostEqual(89.1, results[3]['Confidence'], places=3)

        # verify detect labels
        rek_client.detect_labels.assert_called_once()
        rek_client.detect_labels.assert_called_with(image_bytes=image_list[0],
                                                    bucket=None,
                                                    object_name=None,
                                                    min_confidence=1,
                                                    max_labels=4)

        # verify detect moderation labels
        rek_client.detect_moderation_labels.assert_called_once()
        rek_client.detect_moderation_labels.assert_called_with(image_bytes=image_list[0],
                                                               bucket=None,
                                                               object_name=None,
                                                               min_confidence=1,
                                                               max_labels=4)

        rek_client.search_faces_by_image.assert_called_once()
        rek_client.search_faces_by_image.assert_called_with(image_bytes=image_list[0],
                                                            bucket=None,
                                                            object_name=None,
                                                            face_match_threshold=1,
                                                            max_faces=4)

        rek_client.search_celebrities_by_image.assert_called_once()
        rek_client.search_celebrities_by_image.assert_called_with(image_bytes=image_list[0],
                                                                bucket=None,
                                                                object_name=None,
                                                                face_match_threshold=1,
                                                                max_faces=4)

        # verify sagemaker
        sagemaker_client.detect_labels.assert_called_once()
        sagemaker_client.detect_labels.assert_called_with(image_bytes=image_list[0],
                                                          min_confidence=1)

    def test_detect_image_labels_with_multiple_items(self):
        image_list = [bytearray([1, 2, 3]), bytearray([4, 5, 6])]

        # prepare data
        res_detect_labels1 = [{'Label': 'b', 'Confidence': 40}]
        res_detect_labels2 = [{'Label': 'a', 'Confidence': 30},
                              {'Label': 'c', 'Confidence': 55}]
        res_detect_moderation_labels1 = [
            {'Label': 'a', 'Confidence': 98},
            {'Label': 'd', 'Confidence': 88}]
        res_detect_moderation_labels2 = [
            {'Label': 'e', 'Confidence': 33}]
        res_search_faces_by_image1 = [
            {'Label': 'f', 'Confidence': 22}]
        res_search_faces_by_image2 = [
            {'Label': 'g', 'Confidence': 11},
            {'Label': 'c', 'Confidence': 20}]
        res_sagemaker_detect_labels1 = [{'Label': 'h', 'Confidence': 100}]
        res_sagemaker_detect_labels2 = [{'Label': 'i', 'Confidence': 77}]

        # rek_client
        rek_client = Mock()
        rek_client.detect_labels = MagicMock(
            side_effect=[res_detect_labels1, res_detect_labels2])
        rek_client.detect_moderation_labels = MagicMock(
            side_effect=[res_detect_moderation_labels1, res_detect_moderation_labels2])
        rek_client.search_faces_by_image = MagicMock(
            side_effect=[res_search_faces_by_image1, res_search_faces_by_image2])

        # sagemaker_client
        sagemaker_client = Mock()
        sagemaker_client.detect_labels = MagicMock(
            side_effect=[res_sagemaker_detect_labels1, res_sagemaker_detect_labels2])

        # handler
        handler = ModerationHandler(rek_client=rek_client,
                                    sagemaker_client=sagemaker_client)

        # invoke
        results = handler.detect_image_labels(images=image_list,
                                              return_sources=["DetectLabels", "DetectModerationLabels",
                                                              "FaceSearch", "DetectByCustomModels"],
                                              min_confidence=1,
                                              max_labels=4)

        # verify results
        self.assertEqual(4, len(results))
        # verify label h
        self.assertEqual('h', results[0]['Label'])
        self.assertAlmostEqual(100, results[0]['Confidence'], places=3)
        # verify label a
        self.assertEqual('a', results[1]['Label'])
        self.assertAlmostEqual(98, results[1]['Confidence'], places=3)
        # verify label d
        self.assertEqual('d', results[2]['Label'])
        self.assertAlmostEqual(88, results[2]['Confidence'], places=3)
        # verify label i
        self.assertEqual('i', results[3]['Label'])
        self.assertAlmostEqual(77, results[3]['Confidence'], places=3)

        # verify detect labels
        self.assertEqual(rek_client.detect_labels.call_count, 2)
        detect_labels_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, min_confidence=1, max_labels=4),
            call(image_bytes=image_list[1], bucket=None, object_name=None, min_confidence=1, max_labels=4)]
        rek_client.detect_labels.assert_has_calls(any_order=True,
                                                  calls=detect_labels_calls)

        # verify detect moderation labels
        self.assertEqual(rek_client.detect_moderation_labels.call_count, 2)
        detect_moderation_labels_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, min_confidence=1, max_labels=4),
            call(image_bytes=image_list[1], bucket=None, object_name=None, min_confidence=1, max_labels=4)]
        rek_client.detect_moderation_labels.assert_has_calls(any_order=True,
                                                             calls=detect_moderation_labels_calls)

        # verify search faces
        self.assertEqual(rek_client.search_faces_by_image.call_count, 2)
        search_faces_by_image_calls = [
            call(image_bytes=image_list[0], bucket=None, object_name=None, face_match_threshold=1, max_faces=4),
            call(image_bytes=image_list[1], bucket=None, object_name=None, face_match_threshold=1, max_faces=4)]
        rek_client.search_faces_by_image.assert_has_calls(any_order=True,
                                                          calls=search_faces_by_image_calls)

        sagemaker_detect_labels_calls = [
            call(image_bytes=image_list[0], min_confidence=1),
            call(image_bytes=image_list[1], min_confidence=1)]
        self.assertEqual(sagemaker_client.detect_labels.call_count, 2)
        sagemaker_client.detect_labels.assert_has_calls(calls=sagemaker_detect_labels_calls,
                                                        any_order=True)

    def test_merge_results(self):
        results = ModerationHandler.merge_results(
            [{'Label': 'a', 'Confidence': 30},
             {'Label': 'b', 'Confidence': 40.35},
             {'Label': 'e', 'Confidence': 56},
             {'Label': 'a', 'Confidence': 98.04},
             {'Label': 'd', 'Confidence': 88},
             {'Label': 'c', 'Confidence': 33},
             {'Label': 'f', 'Confidence': 22},
             {'Label': 'g', 'Confidence': 11},
             {'Label': 'c', 'Confidence': 30},
             {'Label': 'c', 'Confidence': 20}],
            max_labels=4)

        self.assertEqual(len(results), 4)
        # verify label a
        self.assertEqual('a', results[0]['Label'])
        self.assertAlmostEqual(98.04, results[0]['Confidence'], places=3)
        # verify label d
        self.assertEqual('d', results[1]['Label'])
        self.assertAlmostEqual(88, results[1]['Confidence'], places=3)
        # verify label c
        self.assertEqual('e', results[2]['Label'])
        self.assertAlmostEqual(56, results[2]['Confidence'], places=3)
        # verify label b
        self.assertEqual('b', results[3]['Label'])
        self.assertAlmostEqual(40.35, results[3]['Confidence'], places=3)

    def test_merge_results_with_less_labels(self):
        results = ModerationHandler.merge_results(
            [{'Label': 'a', 'Confidence': 30},
             {'Label': 'b', 'Confidence': 40.35},
             {'Label': 'b', 'Confidence': 44.35},
             {'Label': 'b', 'Confidence': 88.35},
             {'Label': 'b', 'Confidence': 33.35},
             {'Label': 'b', 'Confidence': 22.35},
             {'Label': 'c', 'Confidence': 55},
             {'Label': 'd', 'Confidence': 12},
             {'Label': 'a', 'Confidence': 98.0}],
            max_labels=9)

        self.assertEqual(len(results), 4)
        # verify label a
        self.assertEqual('a', results[0]['Label'])
        self.assertAlmostEqual(98.0, results[0]['Confidence'], places=3)
        # verify label b
        self.assertEqual('b', results[1]['Label'])
        self.assertAlmostEqual(88.35, results[1]['Confidence'], places=3)
        # verify label c
        self.assertEqual('c', results[2]['Label'])
        self.assertAlmostEqual(55, results[2]['Confidence'], places=3)
        # verify label b
        self.assertEqual('d', results[3]['Label'])
        self.assertAlmostEqual(12, results[3]['Confidence'], places=3)

    def test_camel_to_snake(self):
        self.assertEqual('camel2_camel2_case', ModerationHandler._camel_to_snake('camel2_camel2_case'))
        self.assertEqual('get_http_response_code', ModerationHandler._camel_to_snake('getHTTPResponseCode'))
        self.assertEqual('http_response_code_xyz', ModerationHandler._camel_to_snake('HTTPResponseCodeXYZ'))
        self.assertEqual('detect_labels', ModerationHandler._camel_to_snake('DetectLabels'))
        self.assertEqual('detect_moderation_labels', ModerationHandler._camel_to_snake('DetectModerationLabels'))
        self.assertEqual('face_search', ModerationHandler._camel_to_snake('FaceSearch'))
        self.assertEqual('detect_by_custom_models', ModerationHandler._camel_to_snake('DetectByCustomModels'))
