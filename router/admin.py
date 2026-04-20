from aiogram import Router, types
from aiogram.filters import Command

from core.config import config
from core.filters import IsAdmin

admin_router = Router()
admin_router.message.filter(IsAdmin([config.BOT_ADMIN_ID]))


async def cmd_all(message: types.Message):
    await message.answer("Привет от админ роутера!")


admin_router.message.register(cmd_all, Command("all"))
