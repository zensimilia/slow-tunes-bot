from aiogram import Bot, Router, flags, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import messages
from core.config import config
from db.base import Database
from db.schemas import NewUser
from db.user import create_user, get_users_count
from utils.tg import get_user_url
from utils.version import get_app_version

common_router = Router()


@common_router.message(CommandStart())
@flags.rate_limit(rate=10, key="start")
async def cmd_start(message: types.Message, db: Database) -> None:
    if not message.from_user:
        return

    new_user = NewUser(tg_id=message.from_user.id, username=message.from_user.username)
    user = await db.execute(create_user, new_user)

    text = messages.START_TEXT.format(username=user.username)
    await message.answer(text, disable_notification=True)


@common_router.message(Command("help"))
@flags.rate_limit(rate=10, key="help")
async def cmd_help(message: types.Message) -> None:
    await message.answer(messages.HELP_TEXT, disable_notification=True)


@common_router.message(Command("about", "developer_info", "info"))
@flags.rate_limit(rate=10, key="about")
async def cmd_about(message: types.Message, bot: Bot, db: Database) -> None:
    admin_url = await get_user_url(bot, config.BOT_ADMIN_ID)
    users_count = await db.execute(get_users_count)
    app_version = get_app_version()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text=f"💾 Version {app_version}", url=config.SOURCE_URL))
    keyboard.row(types.InlineKeyboardButton(text="👨‍💻 Admin & Support", url=admin_url))
    keyboard.row(types.InlineKeyboardButton(text="📜 License", url=config.LICENSE_URL))

    text = messages.ABOUT_TEXT.format(
        users_count=users_count,
        slowed_count=0,
        shared_count=0,
    )  # TODO: add real counts of slowed and shared tunes
    await message.answer(text, reply_markup=keyboard.as_markup(), disable_notification=True)
