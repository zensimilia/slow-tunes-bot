class FileIsTooBigError(Exception): ...


class DownloadError(Exception): ...


class UploadError(Exception): ...


class MissingRequiredError(ValueError):
    def __init__(self) -> None:
        super().__init__("There is no required object, key or value")


class NoStreamsError(ValueError):
    def __init__(self) -> None:
        super().__init__("No streams to listen. Call subscribe() first")
