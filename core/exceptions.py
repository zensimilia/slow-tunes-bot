class FileIsTooBigError(Exception): ...


class UnsupportedFormatError(Exception): ...


class DownloadError(Exception): ...


class UploadError(Exception): ...


class MissingRequiredError(ValueError):
    def __init__(self) -> None:
        super().__init__("There is no required object, key or value")
