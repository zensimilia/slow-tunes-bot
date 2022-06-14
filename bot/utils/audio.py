import os

from mutagen import MutagenError, id3
from pydub import AudioSegment
from pydub.exceptions import PydubException
from pydub.utils import mediainfo

from bot.config import AppConfig
from bot.utils.logger import get_logger

config = AppConfig()
log = get_logger()


def slow_down(file_path: str, speed: float = 33 / 45) -> str:
    """This function slow down audio file."""

    slowed_file_path = f'{file_path[:-4]}_slow.mp3'
    try:
        media_info = mediainfo(file_path)
        tags = fill_tags(media_info.get('TAG', {}))

        sound = AudioSegment.from_file(file_path)
        slowed = speed_change(sound, speed)
        slowed.export(
            slowed_file_path,
            format='mp3',
            bitrate=media_info['bit_rate'],
            tags=tags,
        )
        # Add album art cover
        add_album_art(slowed_file_path, config.ALBUM_ART)
    except PydubException as error:
        log.warning(error)
        slowed_file_path = ""

    return slowed_file_path


def speed_change(sound: AudioSegment, speed: float):
    """Change speed of AudioSegment."""

    # Manually override the frame_rate. This tells the computer how many
    # samples to play per second
    sound_with_altered_frame_rate = (
        sound._spawn(  # pylint: disable=protected-access
            sound.raw_data,
            overrides={"frame_rate": int((sound.frame_rate or 1) * speed)},
        )
    )
    # convert the sound with altered frame rate to a standard frame rate
    # so that regular playback programs will work right. They often only
    # know how to play audio at standard frame rate (like 44.1k)
    return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)


def fill_tags(tags: dict) -> dict:
    """Adds extra info to media TAG."""

    extra_title = (tags.get("title", ""), "@slowtunesbot")
    tags.update(
        title=" ".join(extra_title),
        comment="Slowed down to 44/33 rpm by @slowtunesbot",
        encoder="ffmpeg",
    )
    log.debug("Updated media TAG: %s", tags)

    return tags


def brand_file_name(full_path: str) -> str:
    """Returns name of audio file with Bot name and extension."""

    file_name = os.path.splitext(full_path)[0]
    return f"{file_name} @slowtunesbot.mp3"


def add_album_art(audio_file: str, art_file: str) -> bool:
    """Add album art to mp3 audio file."""

    try:
        with open(art_file, "rb") as raw:
            data = raw.read()

        tags = id3.ID3()
        tags.add(
            id3.APIC(
                type=id3.PictureType.COVER_FRONT,
                data=data,
                mime='image/jpeg',
                desc='Cover',
            )
        )
        tags.save(audio_file)

        log.debug("Album art %s added to file %s", art_file, audio_file)
        return True
    except IOError as error:
        log.error("Can't read album art file - %s", error)
        return False
    except MutagenError as error:
        log.error("Can't save album art to file - %s", error)
        return False
