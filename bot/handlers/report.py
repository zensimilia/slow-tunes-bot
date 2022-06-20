from aiogram import types
from aiogram.utils.exceptions import TelegramAPIError

from bot import db, keyboards
from bot.config import AppConfig
from bot.utils.logger import get_logger

log = get_logger()
config = AppConfig()


async def report_confirmation(query: types.CallbackQuery, callback_data: dict):
    """Display confirm Report buttons."""

    await query.answer("Are you sure to report this audio?")

    await query.message.edit_reply_markup(
        keyboards.report_confirm_buttons(callback_data["idc"])
    )


async def report_confiramtion_help(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection HELP at Report confiramtion."""

    await query.answer(
        "Help text there.",
        show_alert=True,
    )


async def report_confiramtion_no(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection NO at Report confiramtion."""

    is_liked = await db.is_liked(callback_data["idc"], query.from_user.id)

    await query.message.edit_reply_markup(
        keyboards.random_buttons(callback_data["idc"], is_like=is_liked)
    )

    await query.answer("Canceled!")


async def report_confiramtion_yes(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection YES at Report confiramtion."""

    if row := await db.get_by_pk("match", callback_data["idc"]):
        (idc, _, file_id, _, _, is_forbidden) = row

        if is_forbidden:
            return await query.answer(
                "This audio is already forbidden", show_alert=True
            )

        log.info(
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
                reply_markup=keyboards.report_response_buttons(idc),
            )

            is_liked = await db.is_liked(idc, query.from_user.id)

            await query.message.edit_reply_markup(
                keyboards.random_buttons(
                    idc,
                    is_like=is_liked,
                )
            )

            return await query.answer(
                "Thanks! Your request is being processed...",
                show_alert=True,
            )
        except TelegramAPIError as error:
            log.error(
                "Can't send Report message to admin <match id=%d> %s",
                idc,
                error,
            )

    raise ValueError(
        f"Can't find row in 'match' table with id={callback_data['idc']}"
    )


async def report_response_accept(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection ACCEPT at Report request."""

    await db.toggle_forbidden(callback_data["idc"], True)

    await query.answer("Success! Audio is forbidden.", show_alert=True)


async def report_response_decline(
    query: types.CallbackQuery, callback_data: dict
):
    """Handler for selection DECLINE at Report request."""

    await db.toggle_forbidden(callback_data["idc"], False)

    await query.answer("Success! Audio is acceptable.", show_alert=True)
