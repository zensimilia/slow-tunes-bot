from mutagen import MutagenError, id3

from .logger import get_logger

log = get_logger()


class Tagging:
    """MP3 ID3 tagging class."""

    def __init__(self, file_path: str) -> None:
        self.__file_path = file_path
        try:
            self.__id3 = id3.ID3(file_path)
        except id3.ID3NoHeaderError:
            self.__id3 = id3.ID3()

    def copy_from(self, source_path: str) -> bool:
        """
        It reads the ID3 tags from the file, and adds them to the current file.
        """

        try:
            source = id3.ID3(source_path)
            for frame in source.values():
                self.__id3.add(frame)
            return True
        except MutagenError as error:
            log.warning(
                "Can't read ID3 tags from file %s - %s",
                source_path,
                error,
            )

        return False

    def add_cover(self, image_path: str, desc: str = None) -> bool:
        """
        It adds the image to the audio file as cover art.
        Only supports JPEG format.
        """

        if data := self.get_image_file(image_path):
            self.__id3.delall('APIC')
            self.__id3.add(
                id3.APIC(
                    type=id3.PictureType.COVER_FRONT,
                    mime='image/jpeg',
                    desc=desc or 'Cover',
                    data=data,
                )
            )
            return True

        return False

    @staticmethod
    def get_image_file(file_path: str) -> bytes | None:
        """
        If the file exists, read it and return the bytes,
        otherwise return None.
        """

        try:
            with open(file_path, "rb") as raw:
                return raw.read()
        except IOError as error:
            log.warning("Can't read image file %s - %s", file_path, error)

        return None

    def save(self, file_path: str = None) -> bool:
        """It tries to save the ID3 tags to the file."""

        try:
            self.__id3.save(file_path or self.__file_path, v2_version=3)
            return True
        except MutagenError as error:
            log.warning(
                "Can't save ID3 tags to the file %s - %s",
                self.__file_path,
                error,
            )

        return False
