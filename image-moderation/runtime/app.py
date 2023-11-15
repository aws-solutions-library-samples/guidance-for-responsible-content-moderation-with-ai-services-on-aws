import os
import logging
import json

from botocore.client import Config
import boto3
from marshmallow import Schema, fields, ValidationError, validate, validates_schema, INCLUDE
from chalice import Chalice, Response, BadRequestError, TooManyRequestsError

from chalicelib import rekognition, moderationhandler, sagemaker
from chalicelib import imagehandler, exception, qrcodehandler
from chalicelib.concurrentutils import Stopwatch
from chalicelib.paramsutils import Strings

app = Chalice(app_name='image-moderation')
app.log.setLevel(logging.DEBUG)

_SESSION = None
_REKOGNITION_CLIENT = None
_SAGEMAKER_CLIENT = None

_MODERATION_BACKEND_SERVICES = [
    "DetectLabels",
    "DetectModerationLabels",
    "FaceSearch",
    "CelebritySearch",
    "DetectByCustomModels",
]

_DEFAULT_LABEL_INCLUSION_FILTERS = ['Military', 'Military Base', 'Military Officer', 'Military Uniform',
                                    'Armor', 'Armored', 'Armory', 'Army', 'Tank', 'War', 'Warplane', 'Soldier',
                                    'Protest', 'Parade', 'Banner', 'Weapon', 'Knife', 'Gun', 'Shotgun',
                                    'Machine Gun', 'QR Code',
                                    'Money', 'Dollar', 'Coin', 'Smoking', 'Alcohol']
_DEFAULT_MODERATION_LABEL_INCLUSION_FILTERS = ['Explicit Nudity', 'Partial Nudity', 'Barechested Male',
                                               'Revealing Clothes', 'Sexual Situations',
                                               'Violence', 'Explosions And Blasts', 'Gambling',
                                               'Army', 'Smoking', 'Drinking', 'Nazi Party']

_STRINGS_HELPER = Strings()

_RETURN_RESOURCES = _STRINGS_HELPER.get_list_from_string(os.environ.get('MODERATION_BACKEND_SERVICES'),
                                                        _MODERATION_BACKEND_SERVICES)

_ENABLE_BLACK_WHITE_LIST = _STRINGS_HELPER.get_bool_from_string(os.environ.get('MODERATION_IMAGE_BLACKLIST_WHITELIST_ENABLED'),
                                                        False)

def get_s3_client():
    return _get_session().client("s3")


def get_image_handler():
    return imagehandler.ImageHandler(s3_client=get_s3_client(),
                                     compress_size=int(os.environ['MODERATION_IMAGE_COMPRESSION_SIZE_THRESHOLD']),
                                     compress_quality_step=int(os.environ['MODERATION_IMAGE_COMPRESS_QUALITY_STEP']),
                                     animation_extraction_size_threshold=int(os.environ['MODERATION_ANIMATION_EXTRACTION_SIZE_THRESHOLD']),
                                     animation_default_small_max_frame=int(os.environ['MODERATION_ANIMATION_EXTRACTION_SMALL_DEFAULT_MAX_THRESHOLD']),
                                     animation_default_large_max_frame=int(os.environ['MODERATION_ANIMATION_EXTRACTION_LARGE_DEFAULT_THRESHOLD_SIZE']),
                                     )


def get_detect_labels_handler():
    return moderationhandler.ModerationHandler(rek_client=get_rekognition_client(),
                                               sagemaker_client=get_sagemaker_client())

def _get_session():
    global _SESSION
    if _SESSION is None:
        _SESSION = boto3.Session()
    return _SESSION


def get_sagemaker_client():
    global _SAGEMAKER_CLIENT
    if _SAGEMAKER_CLIENT is None:
        _SAGEMAKER_CLIENT = sagemaker.SageMakerClient(_get_session().client("sagemaker-runtime"),
                                                      os.environ['SAGEMAKER_ENDPOINT_NAME'])
    return _SAGEMAKER_CLIENT



def get_rekognition_client():
    global _REKOGNITION_CLIENT
    if _REKOGNITION_CLIENT is None:
        config = Config(connect_timeout=5, retries={'max_attempts': 0})
        _REKOGNITION_CLIENT = rekognition.RekognitonClient(
            boto3_client=_get_session().client('rekognition', config=config),
            customer_facial_threshold=_STRINGS_HELPER.get_float_from_string(os.environ.get('MODERATION_CUSTOMER_FACIAL_THRESHOLD'), 85.0),
            celebrity_facial_threshold=_STRINGS_HELPER.get_float_from_string(os.environ.get('MODERATION_CELEBRITY_FACIAL_THRESHOLD'),95.0),
            enable_moderation_filter=_STRINGS_HELPER.get_bool_from_string(os.environ.get('MODERATION_DETECT_MODERATION_LABEL_FILTER_ENABLED'),False),
            label_inclusion_filters=_STRINGS_HELPER.get_list_from_string(os.environ.get('MODERATION_DETECT_LABEL_INCLUSION_FILTER'),_DEFAULT_LABEL_INCLUSION_FILTERS),
            moderation_label_inclusion_filters=_STRINGS_HELPER.get_list_from_string(os.environ.get('MODERATION_DETECT_MODERATION_LABEL_INCLUSION_FILTER'),_DEFAULT_MODERATION_LABEL_INCLUSION_FILTERS),
            collection_id=os.environ['MODERATION_REKOGNITION_COLLECTION_ID'])
    return _REKOGNITION_CLIENT


class BucketObjectSchema(Schema):
    Bucket = fields.String(required=True, validate=validate.Length(min=1, max=256))
    Name = fields.String(required=True, validate=validate.Length(min=1, max=1024))

class ImageSchema(Schema):
    Url = fields.Url()
    Object = fields.Nested(BucketObjectSchema)

    @validates_schema
    def validate_image_info(self, data, **kwargs):
        if 'Url' not in data and 'Object' not in data:
            raise ValidationError('Either of Url or Object is required!')
        if 'Url' in data and 'Object' in data:
            raise ValidationError('Cannot have Url and Object both at the sametime in Image.')

class ListItemSchema(Schema):
    class Meta:
        unknown = INCLUDE

    Image = fields.Nested(nested=ImageSchema, required=True)
    Description = fields.String(validate=lambda s: len(s) <= 1024)

def validate_return_resource(return_resources):
    for return_resource in return_resources:
        if return_resource not in _RETURN_RESOURCES:
            raise ValidationError(f"Return resource {return_resource} not one of {_RETURN_RESOURCES}")

class DetectLabelsSchema(Schema):
    class Meta:
        unknown = INCLUDE

    Image = fields.Nested(nested=ImageSchema, required=True)
    ReturnSource = fields.List(fields.String(), required=False, validate=validate_return_resource)
    MinConfidence = fields.Integer(validate=lambda value: 20 < value <= 100)
    MaxLabels = fields.Integer(required=False, validate=lambda value: 1 <= value <= 4096)

def __get_image(image):
    if image is None:
        return None, None, None

    url_str = image.get('Url')
    if url_str is not None:
        return url_str, None, None

    obj = image.get('Object')

    return None, obj['Bucket'], obj['Name']

# Start to detect list Handlers.
@app.route('/Moderation/DetectImageLabels', methods=['POST'])
def detect_image_labels():
    """Detect image labels"""

    # There's Chalice bug you cannot use app.current_request.json_body for json data as it's not processed in some version
    ## todo check input images
    # json_body = app.current_request.json_body
    app.log.debug("Detect labemls details, request {}, request raw body {}"
                  .format(app.current_request.path, app.current_request.raw_body))
    try:
        body = json.loads(app.current_request.raw_body)
        DetectLabelsSchema().load(body, unknown=None)
    except ValidationError as e:
        app.log.error("Schema error for the request {}, request raw body {}, current request{}: {}"
                      .format(app.current_request.path, app.current_request.raw_body, app.current_request, e.messages))
        raise BadRequestError(e.messages)

    url, bucket, object_name = __get_image(body['Image'])
    min_confidence = body.get('MinConfidence') if body.get('MinConfidence') is not None else 60
    max_labels = body.get('MaxLabels') if body.get('MaxLabels') is not None else 50

    stopwatch = Stopwatch().start()
    labels = _detect_labels(url=url,
                            bucket=bucket,
                            object_name=object_name,
                            return_sources=body.get('ReturnSource'),
                            min_confidence=min_confidence,
                            max_labels=max_labels)
    lapsed = stopwatch.stop()
    app.log.info("Detected finally labels lapsed time {} by {}: {}".format('%.3f' % lapsed, body, labels))
    return {'Labels': labels}


def _qrcode_handle(image_data_list, qrcode_label, url):
    handler = qrcodehandler.QrcodeHandler()
    texts = []

    stopwatch = Stopwatch()
    stopwatch.start()
    app.log.debug(f'Start to extract qrcode info for image from {url}')
    bounding_box = qrcode_label.get('BoundingBox')

    for image_data in image_data_list:
        tmp_texts = handler.decode(image_data, bounding_box)
        if tmp_texts is None or len(tmp_texts) == 0:
            continue

        texts.extend(tmp_texts)
    lapsed = stopwatch.stop()
    app.log.debug(f'End of extracting qrcode info for image lapsed time {lapsed} from {url}')
    qrcode_label['QrcodeData'] = list(set(texts))
    if bounding_box is not None:
        del qrcode_label['BoundingBox']


def _detect_labels(url, bucket, object_name, return_sources, min_confidence, max_labels):
    """
    Facade method to call image handler to get proper images and call moderation handler to detect labels
    """

    image_handler = get_image_handler()
    # download image
    try:
        stopwatch_download = Stopwatch()
        stopwatch_download.start()
        app.log.debug(f'Start handle image from {url}, or {bucket}/{object_name}')
        image_data_list, hash_data = image_handler.image_handler(url,
                                                                 bucket=bucket,
                                                                 object_name=object_name)
        lapsed = stopwatch_download.stop()
        app.log.debug(
            'End of handling image with lapsed time %.3f from %s or %s/%s' % (lapsed, url, bucket, object_name))
    except exception.UnsupportedImageException as e:
        raise BadRequestError(e.message)
    except exception.CannotDownloadImageException as e:
        raise BadRequestError(e.message)
                                        

    # no filter found
    if len(image_data_list) == 0:
        return []

    app.log.debug(f'Start to detect labels for image from {url} or {bucket}/{object_name}')
    # detect labels
    handler = get_detect_labels_handler()
    # detect labels
    stopwatch_detect_labels = Stopwatch()
    stopwatch_detect_labels.start()
    app.log.debug(f'Start to detect labels for resolved image from {url} or {bucket}/{object_name}')
    try:
        labels = handler.detect_image_labels(return_sources=return_sources,
                                             images=image_data_list,
                                             min_confidence=min_confidence,
                                             max_labels=max_labels,
                                             url_hint=url)
    except exception.InvocationException as e:
        app.log.error('Detected labels with backend errors for resolved image from %s or %s/%s' % (
        url, bucket, object_name))
        raise TooManyRequestsError(e.message)

    lapsed = stopwatch_detect_labels.stop()
    qrcode_label = next(filter(lambda label: label['Label'] == 'QR Code', labels), None)
    if qrcode_label is not None:
        _qrcode_handle(image_data_list, qrcode_label, url)
    app.log.debug('Detected labels for resolved image with lapsed time %.3f from %s or %s/%s' % (
        lapsed, url, bucket, object_name))
    return labels
# End of detection Handlers.
