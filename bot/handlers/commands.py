from aiogram import types

from bot import db, keyboards, __version__
from bot.utils.brand import get_caption
from bot.utils.logger import get_logger

log = get_logger()


async def command_random(message: types.Message):
    """Handler for `/random` command. Returns random tune from database."""

    await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

    if random := await db.get_random_match():
        (idc, file_unique_id, file_id, user_id, is_private, *_) = random

        if user_id == message.from_user.id:
            keyboard = keyboards.share_button(
                file_unique_id, is_private=is_private, is_random=True
            )
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


async def next_random(query: types.CallbackQuery, callback_data: dict):
    """Handler for Next button on random tune."""

    if random := await db.get_random_match():
        (idc, file_unique_id, file_id, user_id, is_private, *_) = random

        if str(callback_data["idc"]) in (str(idc), file_unique_id):
            random_count = await db.random_count()
            return (
                await next_random(query, callback_data)
                if (random_count > 1)
                else await query.answer(
                    "Sorry! I have just one of shared tune."
                )
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
        )

        return await query.message.edit_media(
            media,
            reply_markup=keyboard,
        )

    await query.answer("Sorry! I don't have shared tunes yet.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    log.info(
        "User join: %s <%s>", message.from_user.id, message.from_user.username
    )
    await db.add_user(message.from_user.id, message.from_user.username)

    await message.answer(
        "<b>Welcome!</b> Send me the audio track "
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
        "\n\nThis Bot slowing down your audio at 33/45 rpm vinyl ratio. "
        "You can share your result audio with other users by "
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
        "\n\n<b>Statistics:</b>"
        f"\n\nUsers: {users_count}"
        f"\nSlowed tunes: {slowed_count}"
        f"\nShared tunes: {random_count}"
        "\n\n<b>Author:</b> "
        "<a href='https://t.me/zensimilia'>@zensimilia</a>"
        "\n<b>Source</b>: "
        "<a href='https://github.com/zensimilia/slow-tunes-bot'>Github repo</a>"
        f"\nVersion: {__version__}",
        disable_notification=True,
        disable_web_page_preview=True,
    )
