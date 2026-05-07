from typing import TYPE_CHECKING

from aiogram import Bot, Router, flags, types
from aiogram.filters import Command, CommandStart

from bot.core import messages as txt
from bot.keyboards.public import about_keyboard
from db.models.user import UserNew

if TYPE_CHECKING:
    from db.repository.match import MatchStore
    from db.repository.user import UserStore

common_router = Router()


@common_router.message(CommandStart())
@flags.rate_limit(rate=10, key="start")
async def cmd_start(message: types.Message, user_store: UserStore) -> None:
    if not message.from_user:
        return

    user_new = UserNew(tg_id=message.from_user.id, username=message.from_user.username)
    user = await user_store.create(user_new)

    text = txt.START_TEXT.format(username=user.username)
    await message.answer(text, disable_notification=True)


@common_router.message(Command("help"))
@flags.rate_limit(rate=10, key="help")
async def cmd_help(message: types.Message) -> None:
    await message.answer(txt.HELP_TEXT, disable_notification=True)


@common_router.message(Command("about", "developer_info", "info"))
@flags.rate_limit(rate=10, key="about")
async def cmd_about(message: types.Message, bot: Bot, user_store: UserStore, match_store: MatchStore) -> None:
    users_count = await user_store.count()
    slowed_count = await match_store.count()
    public_count = await match_store.count(public_only=True)
    keyboard = await about_keyboard(bot)
    text = txt.ABOUT_TEXT.format(
        users_count=users_count,
        slowed_count=slowed_count,
        public_count=public_count,
    )
    await message.answer(text, reply_markup=keyboard, disable_notification=True)
