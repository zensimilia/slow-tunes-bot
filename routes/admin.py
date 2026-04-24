from aiogram import Router, types
from aiogram.filters import Command

from core.config import config
from core.filters import IsAdmin

admin_router = Router()
admin_router.message.filter(IsAdmin([config.BOT_ADMIN_ID]))


@admin_router.message(Command("all"))
async def cmd_all(message: types.Message) -> None:
    await message.answer("There will be a list of all audios...")
