import asyncio
from sqlite3 import Error as SqliteError

from aiogram import Dispatcher, filters, types
from aiogram.utils.exceptions import FileIsTooBig, MessageNotModified

from bot import db, keyboards
from bot.config import config
from bot.handlers import (
    h_admin,
    h_audio,
    h_commands,
    h_common,
    h_errors,
    h_likes,
    h_report,
    h_share,
)
from bot.utils.u_exceptions import NotSupportedFormat, QueueLimitReached
from bot.utils.u_logger import get_logger
from bot.utils.u_queue import Queue

LOG = get_logger()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    LOG.info("Register Bot handlers...")

    dp.register_errors_handler(
        h_errors.file_is_too_big,
        exception=FileIsTooBig,
    )
    dp.register_errors_handler(
        h_errors.not_supported_format,
        exception=NotSupportedFormat,
    )
    dp.register_errors_handler(
        h_errors.database_error,
        exception=SqliteError,
    )
    dp.register_errors_handler(
        h_errors.message_not_modified_error,
        exception=MessageNotModified,
    )
    dp.register_errors_handler(
        h_errors.queue_limit_reached,
        exception=QueueLimitReached,
    )
    dp.register_errors_handler(
        h_errors.global_error_handler, exception=Exception
    )  # Should be last among errors handlers

    dp.register_message_handler(
        h_commands.command_start,
        commands=["start"],
    )
    dp.register_message_handler(
        h_commands.command_help,
        commands=["help"],
    )
    dp.register_message_handler(
        h_commands.command_about,
        commands=["about", "developer_info"],
    )
    dp.register_message_handler(
        h_commands.command_random,
        commands=["random"],
    )
    dp.register_message_handler(
        h_audio.processing_audio,
        content_types=[types.ContentType.AUDIO],
    )

    # Admin handlers
    dp.register_message_handler(
        h_admin.command_all,
        is_admin=True,
        commands=["all"],
    )
    dp.register_message_handler(
        h_admin.get_tune,
        filters.RegexpCommandsFilter(regexp_commands=["tune_([0-9]*)"]),
        is_admin=True,
    )
    dp.register_callback_query_handler(
        h_admin.tunes_pagging,
        keyboards.tunes_list_cbd.filter(flag="ok"),
    )
    dp.register_message_handler(
        h_admin.command_admin,
        is_admin=True,
        commands=["admin"],
    )

    # Share callback handlers
    dp.register_callback_query_handler(
        h_share.share_confirmation,
        keyboards.share_cbd.filter(action="confirm"),
    )
    dp.register_callback_query_handler(
        h_share.share_confiramtion_help,
        keyboards.share_cbd.filter(action="help"),
    )
    dp.register_callback_query_handler(
        h_share.share_confiramtion_no,
        keyboards.share_cbd.filter(action="no"),
    )
    dp.register_callback_query_handler(
        h_share.share_confiramtion_yes,
        keyboards.share_cbd.filter(action="yes"),
    )

    # Report callback handlers
    dp.register_callback_query_handler(
        h_report.report_confirmation,
        keyboards.random_cbd.filter(action="confirm"),
    )
    dp.register_callback_query_handler(
        h_report.report_confiramtion_help,
        keyboards.random_cbd.filter(action="help"),
    )
    dp.register_callback_query_handler(
        h_report.report_confiramtion_no,
        keyboards.random_cbd.filter(action="no"),
    )
    dp.register_callback_query_handler(
        h_report.report_confiramtion_yes,
        keyboards.random_cbd.filter(action="yes"),
    )

    # Likes and Next callback handlers
    dp.register_callback_query_handler(
        h_likes.toggle_like,
        keyboards.random_cbd.filter(action="toggle_like"),
    )
    dp.register_callback_query_handler(
        h_commands.next_random,
        keyboards.random_cbd.filter(action="next"),
    )

    # Report response callback handlers
    dp.register_callback_query_handler(
        h_report.report_response_accept,
        keyboards.report_response_cbd.filter(action="accept"),
    )
    dp.register_callback_query_handler(
        h_report.report_response_decline,
        keyboards.report_response_cbd.filter(action="decline"),
    )

    dp.register_message_handler(h_common.answer_message)


async def on_startup(dp: Dispatcher):
    """Execute function before Bot start polling."""

    LOG.info("Execute startup Bot functions...")
    db.execute_script("./schema.sql")

    register_handlers(dp)

    commands = [
        types.BotCommand("random", "get some slowed tune"),
        types.BotCommand("help", "if you stuck"),
        types.BotCommand("about", "bot info"),
    ]
    await dp.bot.set_my_commands(commands)

    # Starts loop worker for the queue
    dp.bot.data.update(queue=await Queue.create())
    asyncio.create_task(dp.bot.data["queue"].start())


async def on_shutdown(dp: Dispatcher):
    """Execute function before Bot shut down polling."""

    LOG.info("Execute shutdown Bot functions...")

    # Close Queue connection
    await dp.bot.data["queue"].stop()

    # Close storage
    await dp.storage.close()
    await dp.storage.wait_closed()

    # Clear list of bot commands
    await dp.bot.set_my_commands([])
