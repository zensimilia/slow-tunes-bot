import math

from aiogram import types

from bot import db, keyboards
from bot.keyboards.k_admin import tune_buttons
from bot.utils.u_admin import get_tunes_list, get_username_by_id
from bot.utils.u_logger import get_logger

LOG = get_logger()
ITEMS_ON_PAGE = 10


async def command_admin(message: types.Message):
    """Handler for /admin command."""

    await message.reply(
        "<b>Admin commands:</b>"
        "\n\n/all - list of all tunes."
        "\n/dump - TODO."
        "\n/import - TODO.",
        disable_notification=True,
    )


async def command_all(message: types.Message):
    """Handler for `/all` command. Returns a list of all tunes from database."""

    current_page = 1
    pages = math.ceil(await db.slowed_count() / ITEMS_ON_PAGE)

    if tunes := await db.get_matches(ITEMS_ON_PAGE, 0):
        return await message.answer(
            get_tunes_list(tunes),
            reply_markup=keyboards.tunes_pagging_buttons(current_page, pages),
        )

    LOG.warning("No tunes in database for `/all` command.")
    return await message.reply("Sorry! I don't have any tunes yet.")


async def tunes_pagging(query: types.CallbackQuery, callback_data: dict):
    """Handler for change page in tunes list."""

    page = int(callback_data["page"])
    curr_page = int(callback_data["curr_page"])
    total_pages = math.ceil(await db.slowed_count() / ITEMS_ON_PAGE)

    if curr_page == page:
        return await query.answer()

    if tunes := await db.get_matches(ITEMS_ON_PAGE, ITEMS_ON_PAGE * (page - 1)):
        return await query.message.edit_text(
            get_tunes_list(tunes),
            reply_markup=keyboards.tunes_pagging_buttons(page, total_pages),
        )

    LOG.warning(
        "tunes_pagging: There is no page number <%d>. There are <%d> pages in total.",
        page,
        total_pages,
    )
    return


async def get_tune(message: types.Message, regexp_command):
    """Retrieves a tune based on the given ID and sends it as an audio message."""

    await message.answer_chat_action(types.ChatActions.UPLOAD_AUDIO)

    pk = int(regexp_command.group(1))

    if tune := await db.get_match_by_pk(pk):
        (id_, file_unique_id, file_id, user_id, is_private, *_) = tune
        username = await get_username_by_id(message.bot, user_id)

        is_own = user_id == message.from_user.id
        is_liked = await db.is_liked(id_, message.from_user.id)
        keyboard = tune_buttons(
            id_, file_unique_id, is_private=is_private, is_own=is_own, is_liked=is_liked
        )

        return await message.reply_audio(
            file_id,
            caption=f"Uploaded by {username}",
            reply_markup=keyboard,
        )

    LOG.warning("No tune in database with the given id <%d>", pk)
    return await message.reply("Sorry! There is no tune with the given id.")
