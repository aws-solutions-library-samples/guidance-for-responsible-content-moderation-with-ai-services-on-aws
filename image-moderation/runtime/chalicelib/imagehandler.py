import io
import requests
import hashlib
import random
import logging
from PIL import Image
from .concurrentutils import Stopwatch
from .exception import UnsupportedImageException, CannotDownloadImageException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ImageHandler(object):
    """
    To handle the handle images including download, compress if needed and extract gif framesSimple
    """

    # constructor
    def __init__(self,
                 s3_client=None,
                 compress_size=2 << 18,
                 compress_quality_step=8,
                 animation_extraction_size_threshold=5242880,
                 animation_default_small_max_frame=8,
                 animation_default_large_max_frame=25):
        self._s3_client = s3_client
        self._compress_size = compress_size
        self._compress_quality_step = compress_quality_step
        self._animation_extraction_size_threshold = animation_extraction_size_threshold
        self._animation_default_small_max_frame = animation_default_small_max_frame
        self._animation_default_large_max_frame = animation_default_large_max_frame

    def image_handler(self, url, bucket, object_name):
        """Download image, compress it or extract frames for animated images"""
        stopwatch = Stopwatch()

        # download image
        stopwatch.start()
        logger.debug(f'Start download image from {url}')
        image = self._download_image(url, bucket=bucket, object_name=object_name)
        if image is None or len(image) == 0:
            logger.warning(f'Cannot download image from {url}')
            return [], ''
        lapsed = stopwatch.stop()
        logger.debug('Downloaded image with lapsed time %.3f from %s' % (lapsed, url))

        # detect image format
        logger.debug(f'Start to detect image format for image from {url}')
        image_format, is_animated = self._detect_image_format(image)
        lapsed = stopwatch.stop()
        logger.debug('End of detecting image format for image lapsed %.3f, detected format: %s, url %s' % (lapsed, image_format, url))
        if image_format == 'UNKNOWN' or image_format not in ['PNG', 'JPEG', 'GIF', 'WEBP']:
            logger.error(f'Cannot resolve image with format {image_format} from {url}')
            raise UnsupportedImageException(image_format)

        # handler gif
        image_data_list = [image]
        if is_animated:
            stopwatch.start()
            logger.debug(f'Start to extract animated image for image from {url}')
            image_data_list = self._extract_animation_frame(image)
            lapsed = stopwatch.stop()
            logger.debug('End of extracting animated image for image lapsed %.3f from %s' % (lapsed, url))

        if not is_animated and image_format in ['WEBP', 'GIF']:
            stopwatch.start()
            logger.debug(f'Start to extract animated image for image from {url}')
            image_data_list = [self._transform_to_jpeg(image)]
            lapsed = stopwatch.stop()
            logger.debug('End of extracting animated image for image lapsed %.3f from %s' % (lapsed, url))

        # compress if needed
        resolved_size_list = []
        for image_data in image_data_list:
            if len(image_data) <= self._compress_size:
                resolved_size_list.append(image_data)
                continue

            # compression
            stopwatch.start()
            logger.debug(f'Start to compress image for image from {url}')
            compressed_data = self._compress(image_data, self._compress_size, self._compress_quality_step)
            resolved_size_list.append(compressed_data)
            lapsed = stopwatch.stop()
            logger.debug(
                'End of compressing image from %d to %d for image lapsed %.3f from %s' %
                (len(image_data), len(compressed_data), lapsed, url))

        return resolved_size_list, self._generate_hash(image)

    def generate_hash(self, url='', bucket='', object_name=''):
        # download image
        logger.debug(f'Start download image from {url}')
        image = self._download_image(url, bucket=bucket, object_name=object_name)
        if image is None or len(image) == 0:
            logger.warning(f'Cannot download image from {url}')
            return ''

        return self._generate_hash(image)

    def _download_image(self, url='', bucket='', object_name=''):
        """Download image"""
        try:
            if url is not None:
                with requests.get(url) as res:
                    if res is None or res.content is None:
                        logger.error("Image is empty from %s" % url)
                        return bytearray()
                return res.content

            response = self._s3_client.get_object(Bucket=bucket, Key=object_name)
            if response is None or response.get('Body') is None:
                return bytearray()

            return response['Body'].read()
        except Exception as e:
            raise CannotDownloadImageException(url, bucket, object_name)

    def _detect_image_format(self, image_bytes):
        try:
            with Image.open(io.BytesIO(image_bytes)) as image:
                return image.format, image.is_animated if hasattr(image, 'is_animated') else False
        except:
            return 'UNKNOWN', False

    def _compress(self, image_bytes, transform_to_jpeg=True, compress_quality_step=5, max_target_size=2 << 18):
        """Compress image, currently support jpg/jpeg and png"""
        im_size = len(image_bytes)
        if im_size <= max_target_size:
            return image_bytes

        image_origin = Image.open(io.BytesIO(image_bytes))
        image_format = image_origin.format
        im = image_origin.copy()
        if transform_to_jpeg:
            im = im.convert('RGB')
            image_format = 'jpeg'

        quality = 95
        impressed = None
        while im_size > max_target_size and quality >= 0:
            impressed = io.BytesIO()
            im.save(impressed, format=image_format, quality=quality)
            quality -= compress_quality_step
            im_size = len(impressed.getvalue())

        return impressed.getvalue()

    def _transform_to_jpeg(self, image_bytes):
        """Compress image, currently support jpg/jpeg, png and webp"""
        image_origin = Image.open(io.BytesIO(image_bytes))
        im = image_origin.copy()
        im = im.convert('RGB')
        image_format = 'jpeg'

        impressed = io.BytesIO()
        im.save(impressed, format=image_format)

        return impressed.getvalue()

    def _extract_animation_frame(self, gif_bytes):
        """Return a list of jpeg frame images"""
        with Image.open(io.BytesIO(gif_bytes)) as animation_image:
            # if not gif image, don't do extraction
            if animation_image.format not in ['GIF', 'WEBP']:
                return [gif_bytes]

            total_frames = animation_image.n_frames

            frames = self._generate_frames(len(gif_bytes), self._animation_default_small_max_frame, total_frames, self._animation_default_large_max_frame)

            frames_data = []
            for frame in frames:
                animation_image.seek(frame)
                palette = animation_image.getpalette()
                new_jpeg = Image.new("RGB", animation_image.size)  # generate jpeg
                new_jpeg.paste(animation_image)
                impressed = io.BytesIO()
                new_jpeg.save(impressed, format='jpeg', icc_profile=animation_image.info.get('icc_profile'))
                frames_data.append(impressed.getvalue())

        return frames_data

    def _generate_frames(self, gif_bytes_size, default_max_frame, total_frames, default_large_max_frame=25):
        max_frame = default_max_frame
        if gif_bytes_size >= self._animation_extraction_size_threshold:
            max_frame = default_large_max_frame

        frames = [0]  # envelope frame
        if max_frame == 1:
            pass
        elif total_frames <= max_frame:
            frames = list(range(total_frames))
        else:
            samples = random.sample(list(range(total_frames - 1)), max_frame - 1)
            for sample in sorted(samples):
                frames.append(sample + 1)
        return frames

    def _generate_hash(self, data):
        """
        current support only sha-256 algorith
        """
        if data is None:
            return ""

        algo = hashlib.sha256()
        algo.update(data)
        return algo.hexdigest()
