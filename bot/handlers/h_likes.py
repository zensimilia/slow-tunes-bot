import json

from aiogram import types

from bot import db
from bot.keyboards.k_public import public_buttons
from bot.keyboards.k_random import random_button


async def toggle_like(query: types.CallbackQuery, callback_data: dict):
    """Handler for toggle likes."""

    user_id = query.from_user.id
    is_liked = await db.is_liked(callback_data["idc"], user_id)
    is_random = json.loads(callback_data["is_random"].lower())

    markup = public_buttons(
        callback_data["idc"],
        is_like=not is_liked,
        is_random=is_random,
    )

    if is_random:
        markup.row()
        markup.insert(random_button(callback_data["idc"]))

    await db.toggle_like(not is_liked, callback_data["idc"], user_id)
    await query.message.edit_reply_markup(markup)

    await query.answer("Thanks for like!" if not is_liked else "Audio disliked")
