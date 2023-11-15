import io

from common import img_size, MODEL_FN, INPUT_FN, timed
import torch

model_fn = MODEL_FN
input_fn = INPUT_FN


@timed
def predict_fn(single_data, model):
    """
    Predict a result using a single data

    :param single_data: a single numpy array for an image
    :type single_data: numpy.array
    :param model: the loaded model
    :type model:
    :return:an object with prediction value
    :rtype: object
    """
    try:
        with torch.no_grad():
            pred = model(single_data, size=img_size)

        cb = (
            "xcenter",
            "ycenter",
            "width",
            "height",
            "Confidence",
            "Label",
        )  # xywh columns
        a = [
            dict(zip(cb, x[:5] + [pred.names[int(x[5])]]))
            for x in pred.xywh[0].tolist()
        ]

        return {"CustomLabels": a}

    except Exception as e:
        raise e


if __name__ == "__main__":
    import os
    import json
    import boto3

    model = model_fn(os.path.abspath("../../image-detection/tests/sample_model/"))
    bucket = "image-detection-dev-data7e2128ca-dhh03eqfzxvw"
    file_name = "test_images/flag_0309_4.jpg"
    request_body = json.dumps(
        {
            "bucket": bucket,
            "file_name": file_name,
        }
    )
    input_data = input_fn(request_body, "application/json")
    result = predict_fn(input_data, model)

    s3_client = boto3.client('s3')
    file_byte_string = s3_client.get_object(
        Bucket=bucket, Key=file_name
    )["Body"].read()
    input_data = input_fn(file_byte_string, "application/x-image")
    result = predict_fn(input_data, model)
    print(result)
