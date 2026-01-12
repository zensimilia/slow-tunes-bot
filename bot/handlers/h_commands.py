import random

import aioredis
from aiogram import types

from bot import __version__, db, keyboards
from bot.config import config
from bot.utils.u_brand import get_caption
from bot.utils.u_logger import get_logger

LOG = get_logger()
ITEMS_ON_PAGE = 10
RANDOM_EXPIRE = 60 * 60 * 24  # 24 hours

r = aioredis.Redis(
    host=config.REDIS_HOST, port=config.REDIS_PORT, decode_responses=True
)


async def get_random_match_id(user: str) -> int | None:
    """Get id of the random shared tune from database."""

    key = f"random:{user}"
    match_id = await r.lpop(key)
    if match_id is None:
        ids = await db.get_random_ids()
        pipe = r.pipeline()
        pipe.lpush(key, *ids)
        pipe.expire(key, RANDOM_EXPIRE)
        await pipe.execute()
        return await r.lpop(key)
    return match_id


async def command_random(message: types.Message):
    """Handler for `/random` command. Returns random tune from database."""

    random_id = await get_random_match_id(str(message.from_user.id))
    if random_id is None:
        LOG.info("No tunes in database for /random command")
        return await message.answer("Sorry! I don't have shared tunes yet.")

    if match := await db.get_by_pk("match", int(random_id)):
        await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)
        (idc, file_unique_id, file_id, user_id, is_private, *_) = match

        if user_id == message.from_user.id:
            keyboard = keyboards.share_button(
                file_unique_id, is_private=is_private, is_random=True
            )
        else:
            is_liked = await db.is_liked(idc, message.from_user.id)
            keyboard = keyboards.random_buttons(idc, is_like=is_liked)

        return await message.answer_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboard,
        )

    return await message.answer("Sorry! Something is gone wrong.")


async def next_random(query: types.CallbackQuery, callback_data: dict):
    """Handler for Next button on random tune."""

    random_id = await get_random_match_id(str(query.from_user.id))
    if random_id is None:
        return await query.answer("Sorry! I don't have shared tunes yet.")

    if match := await db.get_by_pk("match", int(random_id)):
        (idc, file_unique_id, file_id, user_id, is_private, *_) = match

        if str(callback_data["idc"]) in (str(idc), file_unique_id):
            random_count = await db.random_count()
            return (
                await next_random(query, callback_data)
                if (random_count > 1)
                else await query.answer("Sorry! I have just one of shared tune.")
            )

        if user_id == query.from_user.id:
            keyboard = keyboards.share_button(
                file_unique_id, is_private=is_private, is_random=True
            )
        else:
            is_liked = await db.is_liked(idc, query.from_user.id)
            keyboard = keyboards.random_buttons(idc, is_like=is_liked)

        media = types.InputMediaAudio(
            file_id,
            caption=await get_caption(),
        )  # type: ignore

        return await query.message.edit_media(
            media,
            reply_markup=keyboard,
        )

    return await query.answer("Sorry! Something is gone wrong.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    LOG.info("User join: %s <%s>", message.from_user.id, message.from_user.username)
    await db.add_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "<b>Welcome!</b> Send me MP3 audio file "
        "or listen other shared tunes by /random command. "
        "Type /help for a list of all commands.",
        disable_notification=True,
    )


async def command_help(message: types.Message):
    """Handler for `/help` command."""

    await message.answer(
        "<b>Available commands:</b>"
        "\n\n/random to get and listen shared tunes."
        "\n/about additional info and author contacts."
        "\n\n<b>How it works:</b>"
        "\n\nThis Bot slowing down your audio at 33/45 vinyl rpm ratio. "
        "You can share your result slowed audio with other users by "
        "<code>share button</code> and promote by <code>like button</code>. "
        "You can also report any shared audio to have it removed "
        "from public access.",
        disable_notification=True,
    )


async def command_about(message: types.Message):
    """Handler for `/about` command."""

    users_count = await db.users_count()
    slowed_count = await db.slowed_count()
    random_count = await db.random_count()

    await message.answer(
        "This bot is written in Python with the aiogram and sox modules. "
        "It uses Redis and SoX services. Enjoy!"
        "\n\n<b>Copyrights notice</b>: "
        "All audio tracks belong to their respective owners "
        "and author of this bot does not claim any right over them. "
        "The uploaded files are stored on the Telegram servers and "
        "are downloaded by the user directly from there."
        f"\n\n<b>Users</b>: {users_count}"
        f"\n<b>Slowed tunes</b>: {slowed_count}"
        f"\n<b>Shared tunes</b>: {random_count}"
        "\n\n<b>Author</b>: "
        "<a href='https://t.me/zensimilia'>@zensimilia</a>"
        "\n<b>Source</b>: "
        "<a href='https://github.com/zensimilia/slow-tunes-bot'>Github</a>"
        f"\n<b>Version</b>: {__version__}",
        disable_notification=True,
        disable_web_page_preview=True,
    )
