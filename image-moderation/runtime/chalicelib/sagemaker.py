import logging
import base64
import json

from .exception import InvocationException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SageMakerClient(object):
    """
    Encapsulates an Amazon SageMaker Client labels. This class is a thin wrapper
    around parts of the Boto3 Amazon Rekognition API.
    """

    def __init__(self, sagemaker_client=None, endpoint_name=""):
        """
        Args:
            :boto3_client: A Boto3 sagemaker client.
        """
        self._sagemaker_client = sagemaker_client
        self._endpoint_name = endpoint_name

    def detect_labels(self, image_bytes, min_confidence=60):
        """
        Send request to sagemaker endpoint to detect labels

        Args:
            :image_bytes: images bytes for detection. if no
        """

        # Do not remove the following lines. It is for auto IAM policy
        # if False:
        #     test = boto3.client('sagemaker-runtime')
        #     test.invoke_endpoint()

        try:
            response = self._sagemaker_client.invoke_endpoint(
                EndpointName=self._endpoint_name,
                ContentType='application/x-image',
                Body=image_bytes,
                Accept='application/json')
        except Exception as e:
            logger.exception(
                "Detect labels by sagemaker endpoint {} has invocation exception with data base64(data): {}".format(
                    self._endpoint_name, base64.b64encode(image_bytes)[0:100]))

            raise InvocationException.from_client_exception(client_exception=e,
                                                            operation_name='Sagemaker_' + self._endpoint_name)

        response = json.loads(response['Body'].read())
        min_confidence_frac = min_confidence / 100

        if response.get('CustomLabels') is None:
            logger.warning('Sagemaker response cannot be parsed: %s' % response)
            return []

        labels = []
        for customer_Label in response.get('CustomLabels'):
            if customer_Label.get('Confidence') is None or customer_Label.get('Label') is None:
                continue

            # filter by min confidence
            if customer_Label['Confidence'] < min_confidence_frac:
                continue

            labels.append({
                'Label': customer_Label['Label'],
                'ReturnSource': 'DetectByCustomModels',
                'Confidence': customer_Label['Confidence'] * 100
            })
        logger.info("Detected labels {} by sagemaker {} with data base64(data): {}".format(
            labels, self._endpoint_name, base64.b64encode(image_bytes)[0:100]))

        sorted_labels = sorted(list(labels), key=lambda item: item['Confidence'], reverse=True)
        return sorted_labels
