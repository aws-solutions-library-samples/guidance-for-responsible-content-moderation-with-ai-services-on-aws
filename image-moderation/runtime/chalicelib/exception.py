from botocore.exceptions import ClientError


class InvocationException(Exception):
    """Error when invoking to use a backend service."""
    MSG_TEMPLATE = (
        'An error occurred ({error_code}) when calling the {operation_name} '
        'with message {error_message}')

    @property
    def operation_name(self):
        return self._operation_name

    @property
    def error_code(self):
        return self._error_code

    @property
    def message(self):
        return self._error_message

    def __init__(self, operation_name, error_code="Unknown", error_message='Unknown'):
        msg = self.MSG_TEMPLATE.format(
            error_code=error_code,
            error_message=error_message,
            operation_name=operation_name
        )
        super(InvocationException, self).__init__(msg)
        self._operation_name = operation_name
        self._error_code = error_code
        self._error_message = error_message

    @classmethod
    def from_client_exception(cls, client_exception, operation_name):
        error_code = type(client_exception).__name__
        error_msg = str(client_exception)
        if hasattr(client_exception, 'response') and client_exception.response is not None:
            client_error = client_exception.response.get('Error')
            if client_error is not None:
                error_code = client_error.get('Code')
                error_msg = client_error.get('Message')
            return InvocationException(operation_name, error_code, error_msg)

        if hasattr(client_exception, 'message'):
            return InvocationException(operation_name, error_code, client_exception.message)
        return InvocationException(operation_name, error_code, error_msg)

    @classmethod
    def backend_exceptions(cls, operation_name='detect_image_labels', error_code='backend_errors', exceptions=[]):
        error_msg = ''
        for exception in exceptions:
            error_msg = error_msg + exception[0] + ' has errors: ' + str(exception[1]) + ', '

        error_msg = '' if len(error_msg)==0 else f"[{error_msg[:-2]}]"
        return InvocationException(operation_name=operation_name, error_code=error_code, error_message=error_msg)


class UnsupportedImageException(Exception):
    @property
    def message(self):
        return self._message

    def __init__(self, image_format):
        msg = f'Unsupported image format {image_format}'
        super(UnsupportedImageException, self).__init__(msg)
        self._message = msg


class CannotDownloadImageException(Exception):
    @property
    def message(self):
        return self._message

    def __init__(self, url, bucket, object_name):
        msg = f'Cannot download image from {url}, {bucket}/{object_name}'
        super(CannotDownloadImageException, self).__init__(msg)
        self._message = msg
