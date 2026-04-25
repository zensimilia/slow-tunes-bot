import io

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from core.config import config


async def get_user_url(bot: Bot, tg_user_id: int) -> str:
    """Return URL to the Telegram user profile."""

    try:
        member = await bot.get_chat_member(chat_id=tg_user_id, user_id=tg_user_id)
    except TelegramAPIError:
        return f"tg://user?id={tg_user_id}"
    return member.user.url


async def get_bot_mention(bot: Bot) -> str:
    """Return string of mention to the Bot."""

    if config.BOT_MENTION:
        return config.BOT_MENTION

    me = await bot.get_me()
    config.BOT_MENTION = f"@{me.username}"
    return config.BOT_MENTION


async def download_file_to_buffer(bot: Bot, file_id: str) -> io.BytesIO:
    buffer = io.BytesIO()
    await bot.download(file=file_id, destination=buffer, seek=True)
    return buffer


async def get_caption_mention(bot: Bot, text: str | None = None) -> str:
    if not text:
        text = "Slowed by "
    mention = await get_bot_mention(bot)
    return f"{text} {mention}"
