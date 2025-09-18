import math

from aiogram import types

from bot import __version__, db, keyboards
from bot.utils.admin import get_tunes_list
from bot.utils.brand import get_caption
from bot.utils.logger import get_logger

log = get_logger()
ITEMS_ON_PAGE = 10


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
        )

        return await query.message.edit_media(
            media,
            reply_markup=keyboard,
        )

    await query.answer("Sorry! I don't have shared tunes yet.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    log.info("User join: %s <%s>", message.from_user.id, message.from_user.username)
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


async def command_all(message: types.Message):
    """Handler for `/all` command. Returns a list of all tunes from database."""

    current_page = 1
    pages = math.ceil(await db.slowed_count() / ITEMS_ON_PAGE)

    if tunes := await db.get_matches(ITEMS_ON_PAGE, 0):
        await message.answer(
            get_tunes_list(tunes),
            reply_markup=keyboards.tunes_pagging_buttons(current_page, pages),
        )
        return

    log.info("No tunes in database for /all command")
    await message.answer("Sorry! I don't have any tunes yet.")


async def tunes_pagging(query: types.CallbackQuery, callback_data: dict):
    """Handler for change page in tunes list."""

    page = callback_data["page"]

    pages = math.ceil(await db.slowed_count() / ITEMS_ON_PAGE)

    if tunes := await db.get_matches(ITEMS_ON_PAGE, ITEMS_ON_PAGE * (int(page) - 1)):
        await query.message.edit_reply_markup(
            keyboards.tunes_pagging_buttons(int(page), pages),
        )
        await query.message.edit_text(
            get_tunes_list(tunes),
        )
        return


async def get_tune(message: types.Message, regexp_command):
    """Retrieves a tune based on a given ID and sends it as an audio message."""

    await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

    id_ = regexp_command.group(1)

    if tune := await db.get_match_by_pk(id_):
        (idc, file_unique_id, file_id, user_id, is_private, *_) = tune

        if user_id == message.from_user.id:
            keyboard = keyboards.share_button(
                file_unique_id, is_private=is_private, is_random=True
            )
        else:
            is_liked = await db.is_liked(idc, message.from_user.id)
            keyboard = keyboards.random_buttons(idc, is_like=is_liked)

        await message.reply_audio(
            file_id,
            caption=await get_caption(),
            reply_markup=keyboard,
        )
        return

    log.info("No tune in database with given id: %d", id_)
    await message.answer("Sorry! There is no tune with given id.")
