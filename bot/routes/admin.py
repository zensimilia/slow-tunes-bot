from aiogram import Bot, Router, types
from aiogram.filters import Command

from bot import messages as txt
from bot.config import config
from bot.core.filters import IsAdmin
from bot.keyboards.public import support_keyboard

admin_router = Router()
admin_router.message.filter(IsAdmin([config.BOT_ADMIN_ID]))


@admin_router.message(Command("admin"), IsAdmin(None))
async def cmd_admin(message: types.Message, bot: Bot) -> None:
    is_admin = IsAdmin([config.BOT_ADMIN_ID])
    if not await is_admin(message):
        keyboard = await support_keyboard(bot)
        await message.answer(txt.ADMIN_RIGHTS_REQUIRED, reply_markup=keyboard)
    await message.answer(txt.ADMIN_LIST)


@admin_router.message(Command("all"))
async def cmd_all(message: types.Message) -> None:
    await message.answer("There will be a list of all audios...")
