import os

from pydub import AudioSegment
from pydub.exceptions import PydubException
from pydub.utils import mediainfo

from bot.config import AppConfig
from bot.utils.logger import get_logger

config = AppConfig()
log = get_logger()


def slow_down(file_path: str, speed: float = 33 / 45) -> str:
    """This function slow down audio file."""

    slowed_file = file_path[:-4] + config.FILE_POSTFIX
    media_info = mediainfo(file_path)
    tags = update_tags(media_info.get('TAG', {}))

    try:
        sound = AudioSegment.from_file(file_path)
        slowed = speed_change(sound, speed)
        slowed.export(
            slowed_file,
            format='mp3',
            bitrate=media_info['bit_rate'],
            tags=tags,
        )
    except PydubException as error:
        log.error(error)
        slowed_file = ""

    return slowed_file


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


def update_tags(tags: dict) -> dict:
    """Updates media TAG by extra info."""

    extra_title = (tags.get('title', ''), '@slowtunesbot')

    tags.update(
        title=" ".join(extra_title),
        comments="Slowed down 44/33 rpm by @slowtunesbot",
    )

    return tags


def brand_file_name(full_path: str) -> str:
    """Returns name of audio file with Bot name and extension."""

    file_name = os.path.splitext(full_path)[0]
    return f"{file_name} @slowtunesbot.mp3"
