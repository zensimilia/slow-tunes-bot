from aiogram import Router, types
from aiogram.filters import Command

from core import messages as txt
from core.config import config
from core.filters import IsAdmin

admin_router = Router()
admin_router.message.filter(IsAdmin([config.BOT_ADMIN_ID]))


@admin_router.message(Command("admin"), IsAdmin(None))
async def cmd_admin(message: types.Message) -> None:
    check_admin = IsAdmin([config.BOT_ADMIN_ID])
    if not await check_admin(message):
        await message.answer(txt.ADMIN_RIGHTS_REQUIRED)
    # TODO @me: add admin message
    await message.answer("Hello, Master! There will be a list of all admin commands...")


@admin_router.message(Command("all"))
async def cmd_all(message: types.Message) -> None:
    await message.answer("There will be a list of all audios...")
