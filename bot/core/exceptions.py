class FileIsTooBigError(Exception):
    """Raised when a file exceeds a certain size limit."""

    def __init__(self, file_size: int) -> None:
        size_mib = file_size / (1024 * 1024)
        super().__init__(f"File size ({size_mib:.2f} MiB) is too big")


class UnsupportedFormatError(Exception): ...


class DownloadError(Exception): ...


class UploadError(Exception): ...


class MissingRequiredError(ValueError, KeyError):
    """Raised when object didn't have required key or value."""

    def __init__(self) -> None:
        super().__init__("There is no required object, key or value")
