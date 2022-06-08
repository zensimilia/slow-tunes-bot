from aiogram import types

from bot.utils.logger import get_logger

log = get_logger()


async def global_error_handler(update: types.Update, error: Exception):
    """Global errors handler."""

    log.error(error)
    await update.message.answer("<b>Error happened!</b>")
    return True


async def file_is_too_big(update: types.Update, _error: Exception):
    """Error handler for FileIsTooBig exception."""

    log.warning(
        "File is too big <file_id=%s file_size=%d>",
        update.message.audio.file_id,
        update.message.audio.file_size,
    )
    await update.message.answer("File is too big. Max file size is 20mb.")
    return True
