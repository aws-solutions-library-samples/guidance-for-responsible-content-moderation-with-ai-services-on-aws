import logging
import base64

from .exception import InvocationException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RekognitonClient(object):
    """
    Encapsulates an Amazon Rekognition detect labels. This class is a thin wrapper
    around parts of the Boto3 Amazon Rekognition API.
    """

    def __init__(self,
                 boto3_client=None,
                 customer_facial_threshold=85,
                 celebrity_facial_threshold=95,
                 enable_moderation_filter=True,
                 label_inclusion_filters=[],
                 moderation_label_inclusion_filters=[],
                 collection_id='face_collection_id'):
        """
        Args:
            :boto3_client: A Boto3 Rekognition client.
        """
        self._boto3_client = boto3_client
        self._customer_facial_threshold = customer_facial_threshold
        self._celebrity_facial_threshold = celebrity_facial_threshold
        self._enable_moderation_filter = enable_moderation_filter
        self._collection_id = collection_id
        self._label_inclusion_filters = label_inclusion_filters
        self._moderation_label_inclusion_filters = moderation_label_inclusion_filters

    @staticmethod
    def _get_json_value_with_default(json_data, key, default):
        if json_data is None or json_data.get(key) is None:
            return default

        return json_data.get(key)

    @staticmethod
    def _get_bounding_box(instances):
        if instances is None or not isinstance(instances, list):
            return None

        for instance in instances:
            if instance.get("BoundingBox") is not None:
                return instance.get("BoundingBox")

        return None

    @staticmethod
    def _get_request_id(response):
        if response is None or response.get('ResponseMetadata') is None:
            return ''

        return response.get('ResponseMetadata').get('RequestId')

    @staticmethod
    def _image_log_bytes_str(image_bytes):
        byte_data = image_bytes if image_bytes is not None else bytearray()
        return base64.b64encode(byte_data)[0:100]

    @property
    def label_inclusion_filters(self):
        return self._label_inclusion_filters

    @property
    def moderation_label_inclusion_filters(self):
        return self._moderation_label_inclusion_filters

    def detect_labels(self, image_bytes, bucket=None, object_name=None, min_confidence=60, max_labels=5):
        """
        DetectLabels

        Args:
            :image_bytes: images bytes for detection. if no
            :bucket: Bucket name of identifies an S3 object as the image source
            :object_name: Object name of identifies an S3 object as the image source
            :min_confidence: The minimum confidence level for the labels to return
        """
        image_bytes_for_log = self._image_log_bytes_str(image_bytes)
        try:
            if image_bytes is not None:
                response = self._boto3_client.detect_labels(
                    Image={
                        'Bytes': image_bytes,
                    },
                    MaxLabels=max_labels,
                    MinConfidence=min_confidence,
                    Settings={
                        'GeneralLabels': {
                            "LabelInclusionFilters": self._label_inclusion_filters
                        },
                    }
                )
            else:
                response = self._boto3_client.detect_labels(
                    Image={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': object_name
                        },
                    },
                    MaxLabels=max_labels,
                    MinConfidence=min_confidence,
                    Settings={
                        'GeneralLabels': {
                            "LabelInclusionFilters": self._label_inclusion_filters
                        },
                    }
                )
        except Exception as e:
            logger.exception(
                "Couldn't detect labels with for base64(data): {} or {}/{}".format(
                    image_bytes_for_log, bucket, object_name))

            raise InvocationException.from_client_exception(client_exception=e,
                                                            operation_name='Rekognition_DetectLabels')

        logger.debug("Detected labels with response {} for base64(data) {} or {}/{} "
                     .format(response,
                             image_bytes_for_log,
                             bucket,
                             object_name))

        # process response
        request_id = self._get_request_id(response)
        labels = []
        for label in response['Labels']:
            if label['Name'] == 'QR Code':
                bounding_box = self._get_bounding_box(label.get('Instances'))
                if bounding_box is not None:
                    labels.append({
                        'Label': label['Name'],
                        'ReturnSource': 'DetectLabels',
                        'Confidence': label['Confidence'],
                        "Suggestion": "pass",
                        "BoundingBox": {
                            "Left": self._get_json_value_with_default(bounding_box, "Left", 0),
                            "Top": self._get_json_value_with_default(bounding_box, "Top", 0),
                            "Width": self._get_json_value_with_default(bounding_box, "Width", 1),
                            "Height": self._get_json_value_with_default(bounding_box, "Height", 1)
                        }
                    })
                    continue

            labels.append({
                'Label': label['Name'],
                'ReturnSource': 'DetectLabels',
                'Confidence': label['Confidence'],
                "Suggestion": "pass"
            })

        logger.debug(
            "Detected labels with rek req id {}, labels {}, base64(data): {} or {}/{}".format(request_id,
                                                                                               labels,
                                                                                               image_bytes_for_log,
                                                                                               bucket, object_name))

        return labels

    def detect_moderation_labels(self, image_bytes, bucket=None, object_name=None, min_confidence=60, max_labels=5):
        """
        DetectModerationLabels

        Args:
            :image_bytes: images bytes for detection. if no
            :bucket: Bucket name of identifies an S3 object as the image source
            :object_name: Object name of identifies an S3 object as the image source
            :min_confidence: The minimum confidence level for the labels to return
        """
        image_bytes_for_log = self._image_log_bytes_str(image_bytes)
        try:
            if image_bytes is not None:
                response = self._boto3_client.detect_moderation_labels(
                    Image={
                        'Bytes': image_bytes,
                    },
                    MinConfidence=min_confidence
                )
            else:
                response = self._boto3_client.detect_moderation_labels(
                    Image={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': object_name
                        },
                    },
                    MinConfidence=min_confidence
                )
        except Exception as e:
            logger.exception("Couldn't detect moderation labels for base64(data): {} or {}/{}"
                             .format(image_bytes_for_log, bucket, object_name))

            raise InvocationException.from_client_exception(client_exception=e,
                                                            operation_name='Rekognition_DetectModerationLabels')

        # process response
        request_id = self._get_request_id(response)
        all_labels = []
        for label in response['ModerationLabels']:
            if self._enable_moderation_filter and label['Name'] not in self._moderation_label_inclusion_filters:
                continue

            all_labels.append({
                'Label': label['Name'],
                'ReturnSource': 'DetectModerationLabels',
                'Confidence': label['Confidence'],
                "Suggestion": "pass"
            })

        # return labels for max labels
        sorted_labels = sorted(all_labels, key=lambda item: item['Confidence'], reverse=True)

        labels = sorted_labels[0:max_labels]
        logger.debug("Detected moderation with rek req id {} labels with labels {}, base64(data): {} or {}/{}"
                     .format(request_id, labels, image_bytes_for_log, bucket, object_name))

        return labels

    def search_faces_by_image(self,
                              image_bytes,
                              bucket=None,
                              object_name=None,
                              face_match_threshold=85,
                              max_faces=5):
        """SearchFacesByImage"""
        match_threshold = max(self._customer_facial_threshold, face_match_threshold)
        image_bytes_for_log = self._image_log_bytes_str(image_bytes)
        try:
            if image_bytes is not None:
                response = self._boto3_client.search_faces_by_image(
                    CollectionId=self._collection_id,
                    FaceMatchThreshold=match_threshold,
                    Image={
                        'Bytes': image_bytes,
                    },
                    MaxFaces=max_faces
                )
            else:
                response = self._boto3_client.search_faces_by_image(
                    CollectionId=self._collection_id,
                    FaceMatchThreshold=match_threshold,
                    Image={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': object_name
                        },
                    },
                    MaxFaces=max_faces
                )
        except Exception as e:
            # suppress no face exception
            if hasattr(e, 'args') and isinstance(e.args, tuple) and 'no faces in the image' in e.args[0]:
                return []

            logger.exception(
                "Couldn't search faces in collection {} for base64(data): {} or {}/{}"
                .format(self._collection_id, image_bytes_for_log, bucket, object_name))

            raise InvocationException.from_client_exception(client_exception=e,
                                                            operation_name='Rekognition_SearchFacesByImage')

        request_id = self._get_request_id(response)
        faces = []
        for face in response['FaceMatches']:
            if face.get('Face') is not None:
                faces.append({
                    'Label': face.get('Face').get('ExternalImageId'),
                    'ReturnSource': 'FaceSearch',
                    'Confidence': face['Similarity'],
                    "Suggestion": "pass"
                })

        logger.debug("Search faces with rek req id {} in collection {} found labels {} for base64(data): {} or {}/{}"
                     .format(request_id,
                             self._collection_id,
                             faces,
                             image_bytes_for_log,
                             bucket, object_name))

        # return labels for max labels
        sorted_faces = sorted(faces, key=lambda item: item['Confidence'], reverse=True)
        return sorted_faces[0:max_faces]

    def _de_duplicate_celebrities(self, faces: list = []):
        # de-duplicate
        deduplicated_faces = []
        for face in faces:
            face_id = face.get('Id')
            if face_id is not None:
                if face_id in [item['Id'] for item in deduplicated_faces]:
                    continue

                # add non duplicated face
                deduplicated_faces.append({
                    'Label': face['Label'],
                    'Id': face['Id'],
                    'ReturnSource': 'CelebritySearch',
                    'Confidence': face['Confidence'],
                    "Suggestion": "pass"
                })

        # remove Id
        for face in deduplicated_faces:
            del face['Id']

        return deduplicated_faces

    def search_celebrities_by_image(self,
                                    image_bytes,
                                    bucket=None,
                                    object_name=None,
                                    face_match_threshold=95,
                                    max_faces=5):
        """RecognizeCelebrities"""
        match_threshold = max(self._celebrity_facial_threshold, face_match_threshold)
        image_bytes_for_log = self._image_log_bytes_str(image_bytes)
        try:
            if image_bytes is not None:
                response = self._boto3_client.recognize_celebrities(
                    Image={
                        'Bytes': image_bytes,
                    }
                )
            else:
                response = self._boto3_client.recognize_celebrities(
                    Image={
                        'S3Object': {
                            'Bucket': bucket,
                            'Name': object_name
                        },
                    }
                )
        except Exception as e:
            logger.exception(
                "Couldn't search celebrities for base64(data): {} or {}/{}"
                .format(image_bytes_for_log, bucket, object_name))

            raise InvocationException.from_client_exception(client_exception=e,
                                                            operation_name='Rekognition_SearchFacesByImage')

        request_id = self._get_request_id(response)
        faces = []
        for face in response['CelebrityFaces']:
            if face.get('MatchConfidence') is not None and face['MatchConfidence'] >= match_threshold:
                faces.append({
                    'Label': face['Name'],
                    'Id': face['Id'],
                    'Confidence': face['MatchConfidence'],
                })

        # sort faces
        sorted_faces = sorted(faces, key=lambda item: item['Confidence'], reverse=True)

        # de-duplicate
        deduplicated_faces = self._de_duplicate_celebrities(faces=sorted_faces)

        logger.debug("Search celebrities with rek req id {} in collection {} found labels {} for base64(data): {} or {}/{}"
                     .format(request_id,
                             self._collection_id,
                             deduplicated_faces,
                             image_bytes_for_log,
                             bucket, object_name))
        return deduplicated_faces[0:max_faces]
