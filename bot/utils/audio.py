import asyncio

from mutagen import MutagenError, id3

from bot.config import AppConfig
from bot.utils.brand import get_tag_comment
from bot.utils.logger import get_logger

from . import soxex

config = AppConfig()
log = get_logger()


async def slow_down(file_path: str, speed: float = 33 / 45) -> str | None:
    """This function slow down audio file."""

    slowed_file_path = f'{file_path[:-4]}_slow.mp3'

    try:
        # tags = await fill_tags(media_info.get('TAG', {}))

        sound = soxex.ExtTransformer()
        sound.speed(speed)
        sound.highpass(100)
        sound.lowpass(8000)
        sound.norm(-1)
        sound.reverb(
            reverberance=speed * 100,
            high_freq_damping=0,
            room_scale=100,
            stereo_depth=50,
        )

        # Run function in separate thread to non-blocking stack
        await asyncio.to_thread(
            sound.build,
            input_filepath=file_path,
            output_filepath=slowed_file_path,
            bitrate=320.0,
        )

        # Add album art cover
        add_album_art(slowed_file_path, config.ALBUM_ART)
    except Exception as error:  # pylint: disable=broad-except
        log.error(error)
        slowed_file_path = None

    return slowed_file_path


async def fill_tags(tags: dict) -> dict:
    """Adds extra info to media TAG."""

    extra_title = (tags.get("title", ""), "@slowtunesbot")
    comment = await get_tag_comment()
    tags.update(
        title=" ".join(extra_title),
        comment=comment,
        encoder="ffmpeg",
    )
    log.debug("Updated media TAG: %s", tags)

    return tags


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

    except MutagenError as error:
        log.error("Can't save album art to file - %s", error)

    return False
