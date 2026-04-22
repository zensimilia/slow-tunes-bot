from aiogram import Bot
from aiogram.exceptions import TelegramAPIError


async def get_user_link(bot: Bot, tg_user_id: int) -> str | None:
    try:
        chat = await bot.get_chat(tg_user_id)
        if chat.username:
            return f"https://t.me/{chat.username}"
        return f"tg://user?id={tg_user_id}"
    except TelegramAPIError:
        return None
