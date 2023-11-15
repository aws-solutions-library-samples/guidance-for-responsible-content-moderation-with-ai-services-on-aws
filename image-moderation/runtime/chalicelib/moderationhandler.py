import logging
import base64
import re
from threading import Thread
from .concurrentutils import ThreadSafeList, CountDownLatch, Stopwatch
from .exception import InvocationException

_RETURN_RESOURCES = [
    "DetectLabels",
    "DetectModerationLabels",
    "CelebritySearch",
    "DetectByCustomModels",
]

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ModerationHandler(object):
    """
    Aggregate the inference apis and invoke parallely and combine the results.
    It will merge and sor the results from each apis and return to the client
    """

    def __init__(self,
                 rek_client=None,
                 sagemaker_client=None):
        self._rek_client = rek_client
        self._sagemaker_client = sagemaker_client

    def detect_image_labels(self,
                            images,
                            bucket=None,
                            object_name=None,
                            return_sources=[],
                            min_confidence=50,
                            max_labels=5,
                            url_hint=''):
        """
        Detect labels

        Args:
            images: bytes list
            bucket: bucket name
            object_name: bucket object name
            return_sources: return source
            min_confidence: min confidence to filter results
            max_labels: maxLabels to return
        Returns:
            Return a list of labels may not have distinct.
        """
        if images is None or len(images) == 0:
            return []

        return_sources = return_sources if return_sources is not None else _RETURN_RESOURCES

        all_results = ThreadSafeList()

        start_signal = CountDownLatch(1)
        done_signal = CountDownLatch(len(return_sources))
        for image in images:
            for return_source in return_sources:
                task_method = getattr(self, 'task_' + self._camel_to_snake(return_source))
                thread = Thread(target=task_method,
                                kwargs={'start_signal': start_signal,
                                        'done_signal': done_signal,
                                        'all_results': all_results,
                                        'image_bytes': image,
                                        'bucket': bucket,
                                        'object_name': object_name,
                                        'min_confidence': min_confidence,
                                        'max_labels': max_labels,
                                        'url_hint': url_hint
                                        })
                thread.start()
            # wait all complete
            start_signal.count_down()
            done_signal.wait()

        if all_results.has_exception():
            raise InvocationException.backend_exceptions(exceptions=all_results.exceptions())

        results_list = self.merge_results(all_results.list(), max_labels=max_labels)
        if len(images) > 0:
            logger.info(
                'Detected labels with for {} image {}, return source {}, min confidence {}, max labels {}, labels: {}'.format(
                    url_hint, base64.b64encode(images[0])[0:100], return_sources, min_confidence, max_labels, results_list))
        else:
            logger.info(
                'Detected labels with image {}/{}, return source {}, min confidence {}, max labels {}, labels: {}'
                .format(bucket, object_name, return_sources, min_confidence, max_labels, results_list))
        return results_list

    def task_detect_labels(self,
                           start_signal,
                           done_signal,
                           all_results: ThreadSafeList,
                           image_bytes,
                           bucket=None,
                           object_name=None,
                           min_confidence=60,
                           max_labels=5,
                           url_hint=''):
        # wait for start signal
        start_signal.wait()
        stopwatch = Stopwatch().start()
        labels = []
        has_error = False
        try:
            labels = self._rek_client.detect_labels(image_bytes=image_bytes,
                                                    bucket=bucket,
                                                    object_name=object_name,
                                                    min_confidence=min_confidence,
                                                    max_labels=max_labels)
        except InvocationException as e:
            lapsed = stopwatch.stop()
            all_results.add_exception('DetectLabels', e)
            has_error = True
            logger.exception(
                "Detected rekognition labels lapsed-error time {} with url {}, min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                    lapsed,
                    url_hint,
                    min_confidence,
                    max_labels,
                    bucket,
                    object_name,
                    e
                ))
        finally:
            # finish this task
            done_signal.count_down()
            all_results.extend(labels)
            if not has_error:
                lapsed = stopwatch.stop()
                logger.info(
                    "Detected rekognition labels lapsed time {} with url {}, min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                        lapsed,
                        url_hint,
                        min_confidence,
                        max_labels,
                        bucket,
                        object_name,
                        labels
                    ))

    def task_detect_moderation_labels(self,
                                      start_signal,
                                      done_signal,
                                      all_results: ThreadSafeList,
                                      image_bytes,
                                      bucket=None,
                                      object_name=None,
                                      min_confidence=60,
                                      max_labels=5,
                                      url_hint=''):
        # wait for start signal
        start_signal.wait()
        stopwatch = Stopwatch().start()
        labels = []
        has_error = False
        try:
            labels = self._rek_client.detect_moderation_labels(image_bytes=image_bytes,
                                                               bucket=bucket,
                                                               object_name=object_name,
                                                               min_confidence=min_confidence,
                                                               max_labels=max_labels)

        except InvocationException as e:
            lapsed = stopwatch.stop()
            all_results.add_exception('DetectModerationLabels', e)
            has_error = True
            logger.info(
                "Detected moderation labels lapsed-error time {} with url {}, min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                    lapsed,
                    url_hint,
                    min_confidence,
                    max_labels,
                    bucket,
                    object_name,
                    e
                ))
        finally:
            # finish this task
            done_signal.count_down()
            all_results.extend(labels)
            if not has_error:
                lapsed = stopwatch.stop()
                logger.info(
                    "Detected moderation labels lapsed time {} with url {}, min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                        lapsed,
                        url_hint,
                        min_confidence,
                        max_labels,
                        bucket,
                        object_name,
                        labels
                    ))

    def task_face_search(self,
                         start_signal,
                         done_signal,
                         all_results: ThreadSafeList,
                         image_bytes,
                         bucket=None,
                         object_name=None,
                         min_confidence=60,
                         max_labels=5,
                         url_hint=''):
        # wait for start signal
        start_signal.wait()
        stopwatch = Stopwatch().start()
        labels = []
        has_error = False
        try:
            labels = self._rek_client.search_faces_by_image(image_bytes=image_bytes,
                                                            bucket=bucket,
                                                            object_name=object_name,
                                                            face_match_threshold=min_confidence,
                                                            max_faces=max_labels)

        except InvocationException as e:
            all_results.add_exception('FaceSearch', e)
            has_error = True
            lapsed = stopwatch.stop()
            logger.info(
                "Detected labels by search faces lapsed-error time {} with url {}, min_confidence {}, "
                "max_labels {}, bucket {}, obj {}: {}".format(
                    lapsed,
                    url_hint,
                    min_confidence,
                    max_labels,
                    bucket,
                    object_name,
                    e
                ))

        finally:
            # finish this task
            done_signal.count_down()
            all_results.extend(labels)
            if not has_error:
                lapsed = stopwatch.stop()
                logger.info(
                    "Detected labels by search faces lapsed time {} with url {}, min_confidence {}, "
                    "max_labels {}, bucket {}, obj {}: {}".format(
                        lapsed,
                        url_hint,
                        min_confidence,
                        max_labels,
                        bucket,
                        object_name,
                        labels
                    ))

    def task_celebrity_search(self,
                              start_signal,
                              done_signal,
                              all_results: ThreadSafeList,
                              image_bytes,
                              bucket=None,
                              object_name=None,
                              min_confidence=60,
                              max_labels=5,
                              url_hint=''):
        # wait for start signal
        start_signal.wait()
        stopwatch = Stopwatch().start()
        labels = []
        has_error = False
        try:
            labels = self._rek_client.search_celebrities_by_image(image_bytes=image_bytes,
                                                                  bucket=bucket,
                                                                  object_name=object_name,
                                                                  face_match_threshold=min_confidence,
                                                                  max_faces=max_labels)
        except InvocationException as e:
            all_results.add_exception('CelebritySearch', e)
            has_error = True
            lapsed = stopwatch.stop()
            logger.info(
                "Detected labels by search celebrities lapsed-error time {} with url {}, min_confidence {}, "
                "max_labels {}, bucket {}, obj {}: {}".format(
                    lapsed,
                    url_hint,
                    min_confidence,
                    max_labels,
                    bucket,
                    object_name,
                    e
                ))
        finally:
            # finish this task
            done_signal.count_down()

            all_results.extend(labels)
            if not has_error:
                lapsed = stopwatch.stop()
                logger.info(
                    "Detected labels by search celebrities lapsed time {} with url {}, min_confidence {}, "
                    "max_labels {}, bucket {}, obj {}: {}".format(
                        lapsed,
                        url_hint,
                        min_confidence,
                        max_labels,
                        bucket,
                        object_name,
                        labels
                    ))

    def task_detect_by_custom_models(self,
                                     start_signal,
                                     done_signal,
                                     all_results: ThreadSafeList,
                                     image_bytes,
                                     bucket=None,
                                     object_name=None,
                                     min_confidence=60,
                                     max_labels=5,
                                     url_hint=''):
        # wait for start signal
        start_signal.wait()
        stopwatch = Stopwatch().start()
        labels = []
        has_error = False
        try:
            labels = self._sagemaker_client.detect_labels(image_bytes=image_bytes,
                                                          min_confidence=min_confidence)

        except InvocationException as e:
            all_results.add_exception('DetectByCustomModels', e)
            has_error = True
            lapsed = stopwatch.stop()
            logger.info(
                "Detected sagemaker custom labels lapsed-error time {} "
                "with url {}, min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                    lapsed,
                    url_hint,
                    min_confidence,
                    max_labels,
                    bucket,
                    object_name,
                    e
                ))
        finally:
            # finish this task
            done_signal.count_down()

            all_results.extend(labels)
            if not has_error:
                lapsed = stopwatch.stop()
                logger.info(
                    "Detected sagemaker custom labels lapsed time {} "
                    "with url {},  min_confidence {}, max_labels {}, bucket {}, obj {}: {}".format(
                        lapsed,
                        url_hint,
                        min_confidence,
                        max_labels,
                        bucket,
                        object_name,
                        labels
                    ))

    @staticmethod
    def merge_results(src_labels: list, max_labels: int = 5):
        # merge labels with max value of label key
        labels_dict = {}
        for label in src_labels:
            if label['Label'] in labels_dict:
                if labels_dict[label['Label']]['Confidence'] >= label['Confidence']:
                    continue

                labels_dict.update({label['Label']: label})
            else:
                labels_dict.update({label['Label']: label})

        sorted_list = sorted(list(labels_dict.values()), key=lambda item: item['Confidence'], reverse=True)
        return sorted_list[0:max_labels]

    @staticmethod
    def _camel_to_snake(name):
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()
