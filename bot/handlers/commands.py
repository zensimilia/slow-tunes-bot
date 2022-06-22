from aiogram import types

from bot import db, keyboards
from bot.utils.brand import get_caption
from bot.utils.logger import get_logger

log = get_logger()


async def command_random(message: types.Message):
    """Handler for `/random` command. Returns random tune from database."""

    await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

    if random := await db.get_random_match():
        (idc, file_unique_id, file_id, user_id, is_private, *_) = random

        if user_id == message.from_user.id:
            keyboard = keyboards.share_button(file_unique_id, is_private)
        else:
            is_liked = await db.is_liked(idc, message.from_user.id)
            keyboard = keyboards.random_buttons(idc, is_like=is_liked)

        await message.answer_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboard,
        )
        return

    log.info("No tunes in database for /random command")
    await message.answer("Sorry! I don't have shared tunes yet.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    log.info(
        "User join: %s <%s>", message.from_user.id, message.from_user.username
    )
    await message.answer("Send me the audio track " "and i will...")
