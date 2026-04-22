from aiogram import Bot, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import messages
from core.config import config
from db.base import Database
from db.schemas import NewUser
from db.user import create_user, get_users_count
from utils.tg import get_user_link
from utils.version import get_version

common_router = Router()


async def cmd_start(message: types.Message, db: Database):
    if not message.from_user:
        return

    new_user = NewUser(tg_id=message.from_user.id, username=message.from_user.username)
    user = await create_user(db, new_user)

    text = messages.START_TEXT.format(username=user.username)
    await message.answer(text, disable_notification=True)


async def cmd_help(message: types.Message):
    await message.answer(messages.HELP_TEXT, disable_notification=True)


async def cmd_about(message: types.Message, bot: Bot, db: Database):
    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text="📜 License", url=config.LICENSE_URL))
    keyboard.row(types.InlineKeyboardButton(text=f"💾 Version {get_version()}", url=config.SOURCE_URL))

    if admin_user_link := await get_user_link(bot, config.BOT_ADMIN_ID):
        keyboard.row(types.InlineKeyboardButton(text="👨‍💻 Admin & Support", url=admin_user_link))

    users_count = await get_users_count(db)
    text = messages.ABOUT_TEXT.format(users_count=users_count)
    await message.answer(text, reply_markup=keyboard.as_markup(), disable_notification=True)


common_router.message.register(cmd_start, CommandStart())
common_router.message.register(cmd_help, Command("help"))
common_router.message.register(cmd_about, Command("about", "developer_info", "info"))
