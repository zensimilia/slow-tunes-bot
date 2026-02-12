import json

from aiogram import types

from bot import db
from bot.keyboards.k_random import random_button
from bot.keyboards.k_share import share_button, share_confirm_buttons


async def share_confirmation(query: types.CallbackQuery, callback_data: dict):
    """Display confirm Share buttons."""

    match = await db.get_match_by_pk(callback_data["idc"])

    if match is not None and match[5]:
        return await query.answer(
            "Sorry! This audio is forbidden to share.", show_alert=True
        )

    # TODO: refactor this - string to boolean conversion
    is_private = json.loads(callback_data["is_private"].lower())
    is_random = json.loads(callback_data["is_random"].lower())

    text = (
        "Are you sure to make this audio public?"
        if is_private
        else "Are you sure to make this audio private?"
    )

    await query.answer(text)

    markup = share_confirm_buttons(
        callback_data["idc"],
        is_private=is_private,
        is_random=is_random,
    )

    if is_random:
        markup.row()
        markup.insert(random_button(callback_data["idc"]))

    await query.message.edit_reply_markup(markup)


async def share_confiramtion_help(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection HELP at Share confiramtion."""

    await query.answer(
        (
            "You can share this audio with other people or keep it private. "
            "Shared audio will be available by /random command."
        ),
        show_alert=True,
    )


async def share_confiramtion_no(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection NO at Share confiramtion."""

    # TODO: refactor this - string to boolean conversion
    is_private = json.loads(callback_data["is_private"].lower())
    is_random = json.loads(callback_data["is_random"].lower())

    markup = share_button(
        callback_data["idc"],
        is_private=is_private,
        is_random=is_random,
    )

    if is_random:
        markup.row()
        markup.insert(random_button(callback_data["idc"]))

    await query.message.edit_reply_markup(markup)

    await query.answer("Canceled!")


async def share_confiramtion_yes(query: types.CallbackQuery, callback_data: dict):
    """Handler for selection YES at Share confiramtion."""

    if row := await db.get_match_by_pk(callback_data["idc"]):
        (idc, _, _, _, is_private, is_forbidden) = row

        if is_forbidden:
            return await query.answer(
                "Sorry! Forbidden to share this audio.",
                show_alert=True,
            )

        # TODO: refactor this - string to boolean conversion
        is_random = json.loads(callback_data["is_random"].lower())

        markup = share_button(
            callback_data["idc"],
            is_private=not is_private,
            is_random=is_random,
        )

        if is_random:
            markup.row()
            markup.insert(random_button(callback_data["idc"]))

        await db.toggle_private(idc, not is_private)
        await query.message.edit_reply_markup(markup)

        return await query.answer("Done!")

    await query.answer("😱 Something went wrong!", show_alert=True)

    raise Exception(f"Can't find match with file_id={callback_data['idc']}")
