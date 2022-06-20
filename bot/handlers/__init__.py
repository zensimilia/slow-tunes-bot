from sqlite3 import Error as SqliteError

from aiogram import Dispatcher, types
from aiogram.utils.exceptions import FileIsTooBig, MessageNotModified

from bot import keyboards
from bot.utils.logger import get_logger

from .audio import processing_audio
from .commands import command_random, command_start
from .common import answer_message
from .errors import (
    database_error,
    file_is_too_big,
    global_error_handler,
    message_not_modified_error,
)
from .likes import toggle_like
from .report import (
    report_confiramtion_help,
    report_confiramtion_no,
    report_confiramtion_yes,
    report_confirmation,
    report_response_accept,
    report_response_decline,
)
from .share import (
    share_confiramtion_help,
    share_confiramtion_no,
    share_confiramtion_yes,
    share_confirmation,
)

log = get_logger()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    log.info("Register Bot handlers...")

    dp.register_errors_handler(
        file_is_too_big,
        exception=FileIsTooBig,
    )
    dp.register_errors_handler(
        database_error,
        exception=SqliteError,
    )
    dp.register_errors_handler(
        message_not_modified_error,
        exception=MessageNotModified,
    )
    dp.register_errors_handler(
        global_error_handler, exception=Exception
    )  # Should be last among errors handlers

    dp.register_message_handler(
        command_start,
        commands=["start"],
    )
    dp.register_message_handler(
        command_random,
        commands=["random"],
    )
    dp.register_message_handler(
        processing_audio,
        content_types=[types.ContentType.AUDIO],
    )

    # Share callback handlers
    dp.register_callback_query_handler(
        share_confirmation,
        keyboards.share_cbd.filter(action="confirm"),
    )
    dp.register_callback_query_handler(
        share_confiramtion_help,
        keyboards.share_cbd.filter(action="help"),
    )
    dp.register_callback_query_handler(
        share_confiramtion_no,
        keyboards.share_cbd.filter(action="no"),
    )
    dp.register_callback_query_handler(
        share_confiramtion_yes,
        keyboards.share_cbd.filter(action="yes"),
    )

    # Report callback handlers
    dp.register_callback_query_handler(
        report_confirmation,
        keyboards.random_cbd.filter(action="confirm"),
    )
    dp.register_callback_query_handler(
        report_confiramtion_help,
        keyboards.random_cbd.filter(action="help"),
    )
    dp.register_callback_query_handler(
        report_confiramtion_no,
        keyboards.random_cbd.filter(action="no"),
    )
    dp.register_callback_query_handler(
        report_confiramtion_yes,
        keyboards.random_cbd.filter(action="yes"),
    )

    # Likes callback handlers
    dp.register_callback_query_handler(
        toggle_like,
        keyboards.random_cbd.filter(action="toggle_like"),
    )

    # Report response callback handlers
    dp.register_callback_query_handler(
        report_response_accept,
        keyboards.report_response_cbd.filter(action="accept"),
    )
    dp.register_callback_query_handler(
        report_response_decline,
        keyboards.report_response_cbd.filter(action="decline"),
    )

    dp.register_message_handler(answer_message)
