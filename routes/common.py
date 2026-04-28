from typing import TYPE_CHECKING

from aiogram import Bot, Router, flags, types
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core import messages as txt
from core.config import config
from db.exceptions import AlreadyExistsError
from schemas.user import UserNew
from utils.sox import SUPPORTED_FMT
from utils.tg import get_user_url
from utils.version import get_app_version

if TYPE_CHECKING:
    from storage.match import MatchStore
    from storage.user import UserStore

common_router = Router()


@common_router.message(CommandStart())
@flags.rate_limit(rate=10, key="start")
async def cmd_start(message: types.Message, user_store: UserStore) -> None:
    if not message.from_user:
        return

    new_user = UserNew(tg_id=message.from_user.id, username=message.from_user.username or "Private Person")
    try:
        user = await user_store.create(new_user)
        await user_store.session.commit()
        username = user.username
    except AlreadyExistsError:
        username = new_user.username

    text = txt.START_TEXT.format(username=username)
    await message.answer(text, disable_notification=True)


@common_router.message(Command("help"))
@flags.rate_limit(rate=10, key="help")
async def cmd_help(message: types.Message) -> None:
    text = txt.HELP_TEXT.format(fmt=", ".join(SUPPORTED_FMT))
    await message.answer(text, disable_notification=True)


@common_router.message(Command("about", "developer_info", "info"))
@flags.rate_limit(rate=10, key="about")
async def cmd_about(message: types.Message, bot: Bot, user_store: UserStore, match_store: MatchStore) -> None:
    admin_url = await get_user_url(bot, config.BOT_ADMIN_ID)
    users_count = await user_store.count()
    slowed_count = await match_store.count()
    public_count = await match_store.count(public_only=True)
    app_version = get_app_version()

    keyboard = InlineKeyboardBuilder()
    keyboard.row(types.InlineKeyboardButton(text="👨‍💻 Admin & Support", url=admin_url))
    keyboard.row(types.InlineKeyboardButton(text=f"💾 Version {app_version}", url=config.SOURCE_URL))
    keyboard.row(types.InlineKeyboardButton(text="📜 License", url=config.LICENSE_URL))

    text = txt.ABOUT_TEXT.format(
        users_count=users_count,
        slowed_count=slowed_count,
        public_count=public_count,
    )
    await message.answer(text, reply_markup=keyboard.as_markup(), disable_notification=True)
