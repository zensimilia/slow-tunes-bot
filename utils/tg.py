import io
from functools import cache

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


async def get_user_url(bot: Bot, tg_user_id: int) -> str:
    """Return URL to the Telegram user profile."""

    try:
        member = await bot.get_chat_member(chat_id=tg_user_id, user_id=tg_user_id)
    except TelegramAPIError:
        return f"tg://user?id={tg_user_id}"
    return member.user.url


@cache
async def get_bot_mention(bot: Bot) -> str:
    """Return string of mention to the Bot."""

    me = await bot.get_me()
    return f"@{me.username}"


async def download_file_to_buffer(bot: Bot, file_id: str) -> io.BytesIO:
    buffer = io.BytesIO()
    await bot.download(file=file_id, destination=buffer, seek=True)
    return buffer


async def get_caption_mention(bot: Bot, text: str | None = None) -> str:
    if not text:
        text = "Slowed by "
    mention = await get_bot_mention(bot)
    return f"{text} {mention}"
