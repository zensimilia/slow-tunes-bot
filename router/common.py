from aiogram import Router, types
from aiogram.filters import Command, CommandStart

from db.base import Database
from db.schemas import GetUser, NewUser
from db.user import create_user

common_router = Router()


async def cmd_start(message: types.Message, db: Database):
    if not message.from_user:
        return
    new_user = NewUser(tg_id=message.from_user.id, username=message.from_user.username)
    user = await create_user(db, new_user)
    await message.answer(
        f"Hello, {user.username} 👋 Send me an <code>MP3</code> file to process your audio, "
        "or try /random to discover a tracks shared by another users. "
        "Use /help to view all commands. <b>Enjoy!</b>"
    )


async def cmd_help(message: types.Message):
    await message.answer("/help")


common_router.message.register(cmd_start, CommandStart())
common_router.message.register(cmd_help, Command("help"))
