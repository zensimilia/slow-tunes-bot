class AppException(Exception):
    """Base exception class for this application."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class QueueLimitReached(AppException):
    """This exception is raised when the queue limit is reached."""


class NotSupportedFormat(AppException):
    """This exception is raised when audio format is not equal to MP3."""
