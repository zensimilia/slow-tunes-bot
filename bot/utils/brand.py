import os

from aiogram import Bot


async def get_bot_mention() -> str:
    """Returns mention to Bot."""

    bot = Bot.get_current()
    bot_info = await bot.get_me()
    return f"@{bot_info.username}"


async def get_caption() -> str:
    """Returns branded caption for audio message."""

    mention = await get_bot_mention()
    return f"Slowed by {mention}"


async def get_branded_file_name(full_path: str) -> str:
    """Returns name of the audio file with Bot name and extension."""

    mention = await get_bot_mention()
    file_name = os.path.splitext(full_path)[0]
    return f"{file_name} {mention}.mp3"


async def get_tag_comment() -> str:
    """Returns branded comment for audio tag."""

    mention = await get_bot_mention()
    return f"Slowed down to 44/33 rpm by {mention}"
