import aioredis
from aiogram import types

from bot import __version__, db
from bot.config import config
from bot.keyboards.k_public import public_buttons
from bot.keyboards.k_random import random_button
from bot.keyboards.k_share import share_button
from bot.utils.u_brand import get_caption
from bot.utils.u_logger import get_logger

LOG = get_logger()
ITEMS_ON_PAGE = 10
RANDOM_EXPIRE = 60 * 60 * 24 * 30  # month in seconds
TEXT_NO_RANDOM_TUNES = "Sorry! There are no public tunes yet."

r = aioredis.Redis(
    host=config.REDIS_HOST,
    port=config.REDIS_PORT,
    decode_responses=True,
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
        return await message.answer(TEXT_NO_RANDOM_TUNES)

    if match := await db.get_by_pk("match", int(random_id)):
        await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)
        (idc, file_unique_id, file_id, user_id, is_private, *_) = match

        if user_id == message.from_user.id:
            keyboard = share_button(
                file_unique_id,
                is_private=is_private,
                is_random=True,
            )
        else:
            is_liked = await db.is_liked(idc, message.from_user.id)
            keyboard = public_buttons(idc, is_like=is_liked, is_random=True)

        keyboard.row()
        keyboard.insert(random_button(idc))

        return await message.reply_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboard,
        )

    return await message.answer("Sorry! Something is gone wrong.")


async def next_random(query: types.CallbackQuery, callback_data: dict):
    """Handler for Next button on random tune."""

    random_id = await get_random_match_id(str(query.from_user.id))
    if random_id is None:
        return await query.answer(TEXT_NO_RANDOM_TUNES)

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
            keyboard = share_button(
                idc,
                is_private=is_private,
                is_random=True,
            )
        else:
            is_liked = await db.is_liked(idc, query.from_user.id)
            keyboard = public_buttons(idc, is_like=is_liked, is_random=True)

        keyboard.row()
        keyboard.insert(random_button(idc))

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
        "<b>Welcome!</b> Send an <code>MP3</code> file to process your audio, "
        "or try /random to discover a random tracks shared by another users. "
        "Use /help to view all commands. <b>Enjoy!</b>",
        disable_notification=True,
    )


async def command_help(message: types.Message):
    """Handler for `/help` command."""

    await message.answer(
        "Send me an <code>MP3</code> audio file "
        "or use one of the following commands:\n\n"
        "/random to get and listen shared tunes.\n"
        "/about additional info and author contacts.\n"
        "/help this help message.\n\n"
        "<b>How it works:</b>\n"
        "This bot adds a vinyl vibe to your audio by adjusting playback speed from 45 to 33 RPM. "
        "You can publish your processed tracks for other users, "
        "support their uploads with likes, "
        "or report any content that shouldn’t remain publicly available.",
        disable_notification=True,
    )


async def command_about(message: types.Message):
    """Handler for `/about` and `/developer_info` command."""

    users_count = await db.users_count()
    slowed_count = await db.slowed_count()
    random_count = await db.random_count()

    return await message.answer(
        f"""This bot is intended for personal and informational use only. For feedback or issues — contact via Telegram. Enjoy!

<b>Author</b>: @zensimilia
<b>Source</b>: <a href='https://github.com/zensimilia/slow-tunes-bot'>Github</a>
<b>Version</b>: {__version__}

<b>Users</b>: {users_count}
<b>Slowed tunes</b>: {slowed_count}
<b>Shared tunes</b>: {random_count}

<b>Copyrights Notice:</b>
All audio tracks and media files belong to their respective owners. The author of this bot does not claim any ownership or rights over the content made available through this bot.

<b>DMCA / Copyright Policy:</b>
This bot acts as a technical intermediary and does not host or store any copyrighted content on its own servers. All uploaded files are stored on Telegram servers and are downloaded by users directly from Telegram. If you are a copyright owner and believe that your rights have been infringed, please contact the developer with relevant information, and the content will be promptly reviewed and removed if necessary.

<b>Terms of Use:</b>
By using this bot, you agree that:
— You are solely responsible for how you use the content obtained via this bot.
— You will comply with all applicable local and international copyright laws.
— The developer is not responsible for user actions or misuse of the bot.
""",
        disable_notification=True,
        disable_web_page_preview=True,
    )
