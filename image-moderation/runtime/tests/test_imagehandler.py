import os
import unittest
from unittest import TestCase, skip
from unittest.mock import Mock, MagicMock, call
from PIL import Image
import boto3

from chalicelib.imagehandler import ImageHandler
from chalicelib.exception import UnsupportedImageException


class TestImages(TestCase):
    """make sure the working dir is {project_root}/code/image-moderation/runtime"""

    def test_handle_image_with_empty_data(self):
        # prepare data
        url = "www.test.example"

        # handler
        handler = ImageHandler()
        handler._download_image = MagicMock(return_value=[])

        # invoke
        empty_list, hashed_key = handler.image_handler(url, None, None)

        self.assertEqual(len(empty_list), 0)
        self.assertEqual(len(hashed_key), 0)
        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)

    def test_handle_image_with_unknown_format(self):
        # prepare data
        url = "www.test.example"
        image_data = bytes('1' * 80000, 'ascii')

        handler = ImageHandler()
        handler._download_image = MagicMock(return_value=image_data)
        handler._detect_image_format = MagicMock(return_value=("UNKNOWN", False))

        # invoke
        with self.assertRaises(UnsupportedImageException) as raised_exception:
            handler.image_handler(url, None, None)

        # verify exception
        self.assertEqual('Unsupported image format UNKNOWN', raised_exception.exception.message)

        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)
        handler._detect_image_format.assert_called_once
        handler._detect_image_format.assert_called_with(image_data)

    def test_handle_image_without_compression_png(self):
        # prepare data
        url = "www.test.example"
        image_data = bytes('1' * 80000, 'ascii')

        handler = ImageHandler(compress_size=len(image_data))
        handler._download_image = MagicMock(return_value=image_data)
        handler._detect_image_format = MagicMock(return_value=("PNG", False))
        handler._compress = MagicMock()

        # invoke
        results, hashed_key = handler.image_handler(url, None, None)

        # verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(hashed_key), 64)
        self.assertEqual(results[0], image_data)

        # verify handler
        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)
        handler._detect_image_format.assert_called_once
        handler._detect_image_format.assert_called_with(image_data)
        # not called compression
        handler._compress.assert_not_called()

    def test_handle_image_with_compression_png(self):
        # prepare data
        url = "www.test.example"

        ## size is wrong
        image_data = bytes('1' * 80000, 'ascii')
        compressed_data = bytes('1' * 8000, 'ascii')

        handler = ImageHandler(compress_size=len(image_data) - 1)
        handler._download_image = MagicMock(return_value=image_data)
        handler._detect_image_format = MagicMock(return_value=["PNG", False])
        handler._compress = MagicMock(return_value=compressed_data)

        # invoke
        results, hashed_key = handler.image_handler(url, None, None)

        # verify results
        self.assertEqual(len(results), 1)
        self.assertEqual(len(hashed_key), 64)
        self.assertEqual(results[0], compressed_data)

        # verify handler
        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)
        handler._detect_image_format.assert_called_once
        handler._detect_image_format.assert_called_with(image_data)
        # not called compression
        handler._compress.assert_called_once
        handler._compress.assert_called_with(image_data, len(image_data) - 1, 8)

    def test_handle_image_without_compression_gif(self):
        # prepare data
        url = "www.test.example"
        image_data = bytes('1' * 80000, 'ascii')
        first_slice = bytes('2' * int(len(image_data) / 2), 'ascii')
        second_slice = bytes('3' * int(len(image_data) / 2), 'ascii')

        handler = ImageHandler(compress_size=len(first_slice))
        handler._download_image = MagicMock(return_value=image_data)
        handler._detect_image_format = MagicMock(return_value=("GIF", True))
        handler._extract_animation_frame = MagicMock(return_value=[first_slice, second_slice])
        handler._compress = MagicMock()

        # invoke
        results, hashed_key = handler.image_handler(url, None, None)

        # verify results
        self.assertEqual(len(results), 2)
        self.assertEqual(len(hashed_key), 64)
        self.assertEqual(results[0], first_slice)
        self.assertEqual(results[1], second_slice)

        # verify handler
        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)
        handler._detect_image_format.assert_called_once
        handler._detect_image_format.assert_called_with(image_data)
        # not called compression
        handler._compress.assert_not_called()

        # gif
        handler._extract_animation_frame.assert_called_once()
        handler._extract_animation_frame.assert_called_with(image_data)

    def test_handle_image_with_compression_gif(self):
        # prepare data
        url = "www.test.example"
        image_data = bytes('1' * 8000, 'ascii')
        compress_size = int(len(image_data) / 2)
        first_slice = bytes('1' * (compress_size + 1), 'ascii')
        second_slice = bytes('2' * (compress_size - 1), 'ascii')
        third_slice = bytes('3' * (compress_size + 2), 'ascii')
        first_compressed = bytes('4' * 100, 'ascii')
        second_compressed = bytes('5' * 200, 'ascii')

        handler = ImageHandler(compress_size=compress_size, compress_quality_step=9)
        handler._download_image = MagicMock(return_value=image_data)
        handler._detect_image_format = MagicMock(return_value=("GIF", True))
        handler._extract_animation_frame = MagicMock(return_value=[first_slice, second_slice, third_slice])
        handler._compress = MagicMock(side_effect=[first_compressed, second_compressed])

        # invoke
        results, hashed_key = handler.image_handler(url, None, None)

        # verify results
        self.assertEqual(len(results), 3)
        self.assertEqual(len(hashed_key), 64)
        self.assertEqual(results[0], first_compressed)
        self.assertEqual(results[1], second_slice)
        self.assertEqual(results[2], second_compressed)

        # verify handler
        handler._download_image.assert_called_once
        handler._download_image.assert_called_with(url, bucket=None, object_name=None)
        handler._detect_image_format.assert_called_once
        handler._detect_image_format.assert_called_with(image_data)

        # gif
        handler._extract_animation_frame.assert_called_once()
        handler._extract_animation_frame.assert_called_with(image_data)

        # compression called
        self.assertEqual(handler._compress.call_count, 2)
        calls = [call(first_slice, compress_size, 9), call(third_slice, compress_size, 9)]
        handler._compress.assert_has_calls(calls=calls)

    @unittest.skipUnless(os.environ.get('RUN_INTEG_TESTS', False),
                         "Skipping integ tests as environment value (RUN_INTEG_TESTS) is not True.")
    def test_download_image(self):
        url = 'https://tse3-mm.cn.bing.net/th/id/OIP-C.4X0mYvBbloVrWyogSLd74wHaHa'
        # create the thread safe list and add items to the list
        image_downloader = ImageHandler()
        content = image_downloader._download_image(url)

        tmp_file = '/tmp/tested_flag.jpg'
        with open(tmp_file, 'wb') as f:
            f.write(content)

        with open(tmp_file, "rb") as image:
            data = image.read()
        self.assertGreater(len(data), 0)

    @unittest.skipUnless(os.environ.get('RUN_INTEG_TESTS', False),
                         "Skipping integ tests as environment value (RUN_INTEG_TESTS) is not True.")
    def test_download_image_with_s3(self):
        bucket = 'do-not-delete-bucket-for-load-test-12-17'
        object_name = 'image_1009.jpg'
        # create the thread safe list and add items to the list
        image_downloader = ImageHandler(boto3.client('s3'))
        content = image_downloader._download_image(None, bucket, object_name)
        tmp_file = '/tmp/tested_flag_s3.jpg'
        with open(tmp_file, 'wb') as f:
            f.write(content)

        with open(tmp_file, "rb") as image:
            data = image.read()
        self.assertGreater(len(data), 0)

    def test_detect_image_format(self):
        resolver = ImageHandler()

        with open('tests/resources/flag.png', "rb") as image:
            png_data = image.read()

        with open('tests/resources/face.jpeg', "rb") as image:
            jpg_data = image.read()

        with open('tests/resources/from_earth_to_the_largest_star.gif', "rb") as image:
            gif_data = image.read()

        unknown_data = bytearray([1, 2, 3, 4, 5, 6])

        self.assertEqual(('PNG', False), resolver._detect_image_format(png_data))
        self.assertEqual(('JPEG', False), resolver._detect_image_format(jpg_data))
        self.assertEqual(('GIF', True), resolver._detect_image_format(gif_data))
        self.assertEqual(('UNKNOWN', False), resolver._detect_image_format(unknown_data))

    def test_compress_png_with_transformation(self):
        file_name = 'tests/resources/flag'
        max_target_size = 1024 * 512

        with open(file_name + '.png', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        compressed_data = resolver._compress(image_bytes=data,
                                             compress_quality_step=30,
                                             transform_to_jpeg=True,
                                             max_target_size=max_target_size)

        with open('/tmp/image_content_moderation_test_flag_' + '2.jpeg', "wb") as file:
            file.write(bytearray(compressed_data))

        with open('/tmp/image_content_moderation_test_flag_' + '2.jpeg', "rb") as image:
            compressed_data = image.read()

        # file must have less data
        self.assertLess(len(compressed_data), max_target_size)

        # jpeg
        with Image.open('/tmp/image_content_moderation_test_flag_' + '2.jpeg') as to_check:
            self.assertEqual(to_check.format, 'JPEG')

    def test_compress_webp_with_transformation(self):
        file_name = 'tests/resources/image'
        max_target_size = 1024 * 12

        with open(file_name + '.webp', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        compressed_data = resolver._compress(image_bytes=data,
                                             compress_quality_step=30,
                                             transform_to_jpeg=True,
                                             max_target_size=max_target_size)

        with open('/tmp/image_content_moderation_test_webp_' + '.jpg', "wb") as file:
            file.write(bytearray(compressed_data))

        with open('/tmp/image_content_moderation_test_webp_' + '.jpg', "rb") as image:
            compressed_read_data = image.read()

        # file must have less data
        self.assertLess(len(compressed_read_data), max_target_size)

        # jpeg
        with Image.open('/tmp/image_content_moderation_test_webp_' + '.jpg') as to_check:
            self.assertEqual(to_check.format, 'JPEG')

    def test_compress_jpg(self):
        file_name = 'tests/resources/flag'
        max_target_size = 1024 * 200

        with open(file_name + '.png', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        compressed_data = resolver._compress(image_bytes=data,
                                             compress_quality_step=10,
                                             max_target_size=max_target_size)

        with open('/tmp/image_content_moderation_test_flag_' + '3.jpeg', "wb") as file:
            file.write(bytearray(compressed_data))

        with open('/tmp/image_content_moderation_test_flag_' + '3.jpeg', "rb") as image:
            compressed_data = image.read()

        # file must have less data
        self.assertLess(len(compressed_data), max_target_size)
        # jpeg
        with Image.open('/tmp/image_content_moderation_test_flag_' + '3.jpeg') as to_check:
            self.assertEqual(to_check.format, 'JPEG')

    def test_compress_png_with_impossible_target_size(self):
        file_name = 'tests/resources/flag'
        max_target_size = 1024 * 512

        with open(file_name + '.png', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        compressed_data = resolver._compress(image_bytes=data,
                                             transform_to_jpeg=False,
                                             compress_quality_step=10,
                                             max_target_size=max_target_size)

        with open('/tmp/image_content_moderation_test_flag_' + '4.png', "wb") as file:
            file.write(bytearray(compressed_data))

        with open('/tmp/image_content_moderation_test_flag_' + '4.png', "rb") as image:
            compressed_data = image.read()

        # file cannot compressed as we expected
        self.assertGreater(len(compressed_data), max_target_size)

        # png
        with Image.open('/tmp/image_content_moderation_test_flag_' + '4.png') as to_check:
            self.assertEqual(to_check.format, 'PNG')

    def test_extract_gif_animation_frame(self):
        file_name = 'tests/resources/from_earth_to_the_largest_star'
        with open(file_name + '.gif', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        extracted_frames = resolver._extract_animation_frame(data)
        i = 0
        for extracted_frame in extracted_frames:
            i += 1
            # file data cannot be empty
            self.assertGreater(len(extracted_frame), 100)
            with open('/tmp/from_earth_to_the_largest_star_%d.jpeg' % i, "wb") as file:
                file.write(bytearray(extracted_frame))

            with Image.open('/tmp/from_earth_to_the_largest_star_%d.jpeg' % i) as to_check:
                self.assertEqual(to_check.format, 'JPEG')

    def test_extract_webp_animation_frame(self):
        file_name = 'tests/resources/animate'
        with open(file_name + '.webp', "rb") as image:
            data = image.read()

        resolver = ImageHandler()

        extracted_frames = resolver._extract_animation_frame(data)
        i = 0
        for extracted_frame in extracted_frames:
            i += 1
            # file data cannot be empty
            self.assertGreater(len(extracted_frame), 100)
            with open('/tmp/moderation_animate_%d.jpeg' % i, "wb") as file:
                file.write(bytearray(extracted_frame))

            with Image.open('/tmp/moderation_animate_%d.jpeg' % i) as to_check:
                self.assertEqual(to_check.format, 'JPEG')

    def test_extract_frames_max_frame_less_than_total(self):
        resolver = ImageHandler()
        frames = resolver._generate_frames(5 * 1024 * 1024, default_max_frame=15, total_frames=10)

        # verify
        self.assertEqual(list(range(10)), frames)

    def test_extract_frames_max_frame_greater_than_total(self):
        resolver = ImageHandler()
        frames = resolver._generate_frames(5 * 1024 * 1024-1, default_max_frame=8, total_frames=200)

        # verify sorted sorted
        copied = list(frames)
        copied.sort()
        self.assertEqual(copied, frames)

        # verify
        self.assertEqual(8, len(frames))

    def test_extract_frames_max_frame_greater_than_total(self):
        resolver = ImageHandler()
        frames = resolver._generate_frames(5 * 1024 * 1024+1, default_max_frame=8, total_frames=200)

        # verify sorted sorted
        copied = list(frames)
        copied.sort()
        self.assertEqual(copied, frames)

        # verify
        self.assertEqual(25, len(frames))

    def test_extract_frames_always_have_envelope(self):
        resolver = ImageHandler()
        size = 5 * 1024 * 1024-500
        # verify first one always is 0
        for i in range(1000):
            frames = resolver._generate_frames(size+i, default_max_frame=10, total_frames=20)
            self.assertEqual(frames[0], 0)

    def test_generate_hash_with_None(self):
        handler = ImageHandler()

        generate_hash = handler._generate_hash(None)

        # verify
        self.assertEqual("", generate_hash)

    def test_generate_hash_with_empty(self):
        empty_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

        handler = ImageHandler()
        generate_hash = handler._generate_hash(bytearray())

        # verify
        self.assertEqual(empty_hash, generate_hash)

    def test_generate_hash_with_data(self):
        handler = ImageHandler()

        # verify first one always is 0
        generate_hash = handler._generate_hash(bytearray([1, 2, 2, 2]))

        self.assertEqual(64, len(generate_hash))
