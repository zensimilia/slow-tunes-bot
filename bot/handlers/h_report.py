import json

from aiogram import types
from aiogram.utils.exceptions import TelegramAPIError

from bot import db
from bot.config import config
from bot.keyboards.k_public import (
    public_buttons,
    report_confirm_buttons,
    report_response_buttons,
)
from bot.keyboards.k_random import random_button
from bot.utils.u_logger import get_logger

LOG = get_logger()


async def report_confirmation(query: types.CallbackQuery, callback_data: dict):
    """Display confirm Report buttons."""

    await query.answer("Are you sure to report this audio?")

    is_random = json.loads(callback_data["is_random"].lower())

    markup = report_confirm_buttons(
        callback_data["idc"],
        is_random=is_random,
    )

    if is_random:
        markup.row()
        markup.insert(random_button(callback_data["idc"]))

    await query.message.edit_reply_markup(markup)


async def report_confiramtion_help(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection HELP at Report confiramtion."""

    await query.answer(
        (
            "Send an audio ban request to a moderator. "
            "Banned audio is unavailable by /random command."
        ),
        show_alert=True,
    )


async def report_confiramtion_no(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection NO at Report confiramtion."""

    is_liked = await db.is_liked(callback_data["idc"], query.from_user.id)
    is_random = json.loads(callback_data["is_random"].lower())

    markup = public_buttons(
        callback_data["idc"],
        is_like=is_liked,
        is_random=is_random,
    )

    if is_random:
        markup.row()
        markup.insert(random_button(callback_data["idc"]))

    await query.message.edit_reply_markup(markup)

    return await query.answer("Canceled!")


async def report_confiramtion_yes(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection YES at Report confiramtion."""

    if row := await db.get_match_by_pk(callback_data["idc"]):
        (idc, _, file_id, _, _, is_forbidden) = row

        if is_forbidden:
            return await query.answer(
                "This audio is already forbidden", show_alert=True
            )

        LOG.info(
            "NEW REPORT TO AUDIO <file_id=%s user_id=%d>",
            file_id,
            query.from_user.id,
        )

        mention = f"<a href='tg://user?id={query.from_user.id}'>{query.from_user.username}</a>"

        try:
            await query.bot.send_audio(
                config.ADMIN_ID,
                file_id,
                caption=f"Hola! {mention} report this audio. What should we do whith this request?",
                reply_markup=report_response_buttons(idc),
            )

            is_liked = await db.is_liked(idc, query.from_user.id)
            is_random = json.loads(callback_data["is_random"].lower())

            markup = public_buttons(
                idc,
                is_like=is_liked,
                is_random=is_random,
            )

            if is_random:
                markup.row()
                markup.insert(random_button(callback_data["idc"]))

            await query.message.edit_reply_markup(markup)

            return await query.answer(
                "Thanks! Your request is being processed...",
                show_alert=True,
            )
        except TelegramAPIError as error:
            LOG.error(
                "Can't send Report message to admin <match id=%d> %s",
                idc,
                error,
            )

    raise ValueError(f"Can't find row in 'match' table with id={callback_data['idc']}")


async def report_response_accept(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection ACCEPT at Report request."""

    await db.toggle_forbidden(callback_data["idc"], True)

    return await query.answer("Success! Audio is forbidden.", show_alert=True)


async def report_response_decline(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection DECLINE at Report request."""

    await db.toggle_forbidden(callback_data["idc"], False)

    return await query.answer("Success! Audio is acceptable.", show_alert=True)
