import json

from aiogram import types

from bot import keyboards, db


async def share_confirmation(query: types.CallbackQuery, callback_data: dict):
    """Display confirm Share buttons."""

    (_, _, _, _, _, is_forbidden) = await db.get_match(callback_data["file_id"])

    if is_forbidden:
        return await query.answer(
            "Sorry! This audio is forbidden to share.", show_alert=True
        )

    is_private = json.loads(callback_data["is_private"].lower())
    text = (
        "Are you sure to make this audio public?"
        if is_private
        else "Are you sure to make this audio private?"
    )

    await query.answer(text)

    await query.message.edit_reply_markup(
        keyboards.share_confirm_buttons(
            callback_data["file_id"],
            is_private,
        )
    )


async def share_confiramtion_help(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection HELP at Share confiramtion."""

    await query.answer(
        (
            "You can share this audio with other people or keep it private. "
            "Shared audio will be available by /random command."
        ),
        show_alert=True,
    )


async def share_confiramtion_no(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection NO at Share confiramtion."""

    is_private = json.loads(callback_data["is_private"].lower())

    await query.message.edit_reply_markup(
        keyboards.share_button(
            callback_data["file_id"],
            is_private,
        )
    )

    await query.answer("Canceled!")


async def share_confiramtion_yes(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection YES at Share confiramtion."""

    if row := await db.get_match(callback_data["file_id"]):
        (idc, _, _, _, is_private, is_forbidden) = row

        if is_forbidden:
            return await query.answer(
                "Sorry! Forbidden to share this audio.",
                show_alert=True,
            )

        await db.toggle_private(idc, not is_private)
        await query.message.edit_reply_markup(
            keyboards.share_button(
                callback_data["file_id"],
                not is_private,
            )
        )

        return await query.answer("Done!")

    await query.answer("😱 Something went wrong!", show_alert=True)

    raise Exception(f"Can't find match with file_id={callback_data['file_id']}")
