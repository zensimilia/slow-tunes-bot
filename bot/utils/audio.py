import asyncio

from bot.config import AppConfig
from bot.utils.brand import get_tag_comment
from bot.utils.logger import get_logger
from bot.utils.tagging import Tagging

from .soxex import ExtTransformer

config = AppConfig()
log = get_logger()


async def slow_down(file_path: str, speed: float = 33 / 45) -> str | None:
    """This function slow down audio file."""

    slowed_file_path = f'{file_path[:-4]}_slow.mp3'

    try:
        chain = ExtTransformer()
        chain.speed(speed)
        chain.highpass(100)
        chain.lowpass(8000)
        chain.norm(-1)
        chain.reverb(
            reverberance=speed * 100,
            high_freq_damping=0,
            room_scale=100,
            stereo_depth=50,
        )

        # Run function in separate thread to non-blocking stack
        await asyncio.to_thread(
            chain.build,
            input_filepath=file_path,
            output_filepath=slowed_file_path,
            bitrate=320.0,
        )

        tags = Tagging(slowed_file_path)
        tags.copy_from(file_path)
        tags.add_cover(config.ALBUM_ART)
        tags.save()

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
