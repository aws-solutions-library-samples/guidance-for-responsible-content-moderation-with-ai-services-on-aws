import logging
import io
from pyzbar.pyzbar import decode
from PIL import Image

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class QrcodeHandler(object):
    """
    Read QRCode
    """

    # constructor
    def __init__(self):
        pass

    def decode(self, image_bytes, bounding_box=None, margin=1.2):
        """Decode qrcode image, currently support jpg/jpeg and png
            bounding_box = (Left, Top, Width, Height)
        """
        image = Image.open(io.BytesIO(image_bytes))
        if bounding_box is not None:
            box = self._get_crop_data_with_margin(bounding_box, image.size, margin)
            image = image.crop(box)

        decoded_list = decode(image)
        if decoded_list is None or len(decoded_list) == 0:
            return []

        results = []
        for obj in decoded_list:
            # draw the barcode
            if obj.data is not None:
                results.append(obj.data.decode())

        return results

    def _get_crop_data_with_margin(self, bounding_box, image_size, margin):
        left = bounding_box['Left'] * image_size[0]
        top = bounding_box['Top'] * image_size[1]
        width = bounding_box['Width'] * image_size[0] * margin
        height = bounding_box['Height'] * image_size[1] * margin

        right = left + width
        lower = top + height
        if right >= image_size[0]:
            right = image_size[0]
        elif right <= left:
            right = left

        if lower >= image_size[0]:
            lower = image_size[1]
        elif lower <= top:
            lower = top

        return (left, top, right, lower)
