from aiogram import Bot, Router, flags, types
from aiogram.filters import Command, CommandStart

from bot import messages as txt
from bot.keyboards.public import about_keyboard
from models import Match, User

common_router = Router()


@common_router.message(CommandStart())
@flags.rate_limit(rate=10, key="start")
async def cmd_start(message: types.Message) -> None:
    if not message.from_user:
        return

    if user := await User.objects().get(User.tg_id == message.from_user.id):
        user.username = message.from_user.username
    else:
        user = User(
            tg_id=message.from_user.id,
            username=message.from_user.username,
        )
    await user.save()

    text = txt.START_TEXT.format(username=user.username)
    await message.answer(text, disable_notification=True)


@common_router.message(Command("help"))
@flags.rate_limit(rate=10, key="help")
async def cmd_help(message: types.Message) -> None:
    await message.answer(txt.HELP_TEXT, disable_notification=True)


@common_router.message(Command("about", "developer_info", "info"))
@flags.rate_limit(rate=10, key="about")
async def cmd_about(message: types.Message, bot: Bot) -> None:
    users_count = await User.count()
    slowed_count = await Match.count()
    public_count = await Match.count().where(
        Match.is_private.eq(False),  # noqa: FBT003
        Match.is_forbidden.eq(False),  # noqa: FBT003
    )

    keyboard = await about_keyboard(bot)
    text = txt.ABOUT_TEXT.format(
        users_count=users_count,
        slowed_count=slowed_count,
        public_count=public_count,
    )
    await message.answer(text, reply_markup=keyboard, disable_notification=True)
