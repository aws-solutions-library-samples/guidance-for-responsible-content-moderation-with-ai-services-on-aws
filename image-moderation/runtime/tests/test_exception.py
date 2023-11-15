import unittest
from chalicelib.exception import InvocationException, UnsupportedImageException, CannotDownloadImageException


class TestException(unittest.TestCase):
    def test_invocation_exception(self):
        with self.assertRaises(InvocationException) as raised_exception:
            raise InvocationException('test-operation', '200', 'test message')

        # verify exception
        self.assertEqual(raised_exception.exception.operation_name, 'test-operation')
        self.assertEqual(raised_exception.exception.error_code, '200')
        self.assertEqual(raised_exception.exception.message, 'test message')

    def test_from_client_exception(self):
        with self.assertRaises(InvocationException) as raised_exception:
            raise InvocationException.from_client_exception(Exception('error_msg_for_test'), 'test-operation')

        # verify exception
        self.assertEqual(raised_exception.exception.operation_name, 'test-operation')
        self.assertEqual(raised_exception.exception.error_code, 'Exception')
        self.assertEqual(raised_exception.exception.message, 'error_msg_for_test')

    def test_backend_exceptions(self):
        with self.assertRaises(InvocationException) as raised_exception:
            raise InvocationException.backend_exceptions(exceptions=[('op1', Exception('ex_op1')), ('op2', Exception('ex_op2'))])

        # verify exception
        self.assertEqual(raised_exception.exception.message, '[op1 has errors: ex_op1, op2 has errors: ex_op2]')
        self.assertEqual(raised_exception.exception.error_code, 'backend_errors')
        self.assertEqual(raised_exception.exception.operation_name, 'detect_image_labels')

    def test_unsupported_exception(self):
        with self.assertRaises(UnsupportedImageException) as raised_exception:
            raise UnsupportedImageException('test-format')

        # verify exception
        self.assertEqual(raised_exception.exception.message, 'Unsupported image format test-format')

    def test_download_exception(self):
        with self.assertRaises(CannotDownloadImageException) as raised_exception:
            raise CannotDownloadImageException('www.bef.com', 'bucket1', '123')

        # verify exception
        self.assertEqual(raised_exception.exception.message, 'Cannot download image from www.bef.com, bucket1/123')
