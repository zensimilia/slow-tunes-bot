from aiogram import types

from bot.utils.logger import get_logger

log = get_logger()


async def global_error_handler(update: types.Update, error: Exception):
    """Global errors handler."""

    log.error("(%s) %s", error.__class__.__name__, error)
    text = "😱 Something wrong happened! Please try again or come back later..."

    if update.message is not None:
        await update.message.reply(text)
    elif update.callback_query is not None:
        await update.callback_query.answer(text, show_alert=True)
    return True


async def file_is_too_big(update: types.Update, _error: Exception):
    """Error handler for FileIsTooBig exception."""

    log.warning(
        "File is too big <file_id=%s file_size=%d>",
        update.message.audio.file_id,
        update.message.audio.file_size,
    )
    await update.message.reply("💾 File is too big. Max file size is 20 MB.")
    return True


async def not_supported_format(update: types.Update, _error: Exception):
    """Error handler for NotSupportedFormat exception."""

    log.info(
        "Not supported audio format <file_extension=%s>",
        update.message.audio.file_name[-3:],
    )
    await update.message.reply("✋ Sorry! Only MP3 files can be processed.")
    return True


async def database_error(update: types.Update, _error: Exception):
    """Error handler for database Error exception."""

    text = "🚧 I have some issues with the database. Please come back later..."

    if update.message is not None:
        await update.message.reply(text)
    elif update.callback_query is not None:
        await update.callback_query.answer(text, show_alert=True)
    return True


async def message_not_modified_error(_update: types.Update, error: Exception):
    """Error handler for MessageNotModified exception."""

    log.warning(error)
    return True


async def queue_limit_reached(update: types.Update, error: Exception):
    """Error handler for QueueLimitReached exception."""

    log.debug(
        "User <user_id=%d> has reached his queue limit. Active tasks: %d",
        update.message.from_user.id,
        error,
    )
    await update.message.reply(
        (
            "✋ You've reached your queue limit. "
            "Wait until the previous tasks are ready and try again."
        )
    )
    return True
