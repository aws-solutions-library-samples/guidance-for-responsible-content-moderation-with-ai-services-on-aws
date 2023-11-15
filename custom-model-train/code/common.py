import os

import botocore
from PIL import Image
from functools import wraps
from time import time
import torch
import boto3
import logging
from yolov5.models.experimental import attempt_load
from yolov5.models.common import AutoShape
import numpy as np
from io import BytesIO
import cv2
import json

from yolov5.utils.dataloaders import exif_transpose

client_config = botocore.config.Config(
    max_pool_connections=50
)

s3_client = boto3.client("s3", config=client_config)
img_size = 640

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("SAGEMAKER_LOGGING_LEVEL", logging.INFO))

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def timed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        elapsed = time() - start
        logger.debug("%s took %f time to finish" % (f.__name__, elapsed))
        return result

    return wrapper


@timed
def MODEL_FN(model_dir):
    loaded_model = attempt_load(os.path.join(model_dir, "best.pt"))
    loaded_model = AutoShape(loaded_model)

    loaded_model.to(DEVICE)
    loaded_model.eval()

    return loaded_model


@timed
def INPUT_FN(input_data, request_content_type):
    #  The request_body is coming 1 by 1
    """An input_fn that loads a pickled tensor"""

    if request_content_type == "application/json":
        try:

            json_request = json.loads(input_data)

            file_byte_string = s3_client.get_object(
                Bucket=json_request["bucket"], Key=json_request["file_name"]
            )["Body"].read()

            im = Image.open(BytesIO(file_byte_string))
            im = im.convert("RGB")
            im = np.array(exif_transpose(im))

            return im
        except Exception as e:
            raise e
    elif request_content_type == "application/x-image":
        im = Image.open(BytesIO(input_data))
        im = im.convert("RGB")
        return np.array(exif_transpose(im))
    else:
        # Handle other content-types here or raise an Exception
        # if the content type is not supported.
        raise Exception("Unsupported content type")



