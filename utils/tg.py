import io
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram import Bot, types
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from core.config import config
from core.exceptions import MissingRequiredError
from keyboards.public import please_wait_button

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

REPLY_AUDIO_FX = "5104841245755180586"  # fire


async def get_user_url(bot: Bot, tg_user_id: int) -> str:
    """
    Generates a direct URL to a Telegram user's profile.

    Attempts to fetch the user's information via 'get_chat_member' to obtain
    a public link (if available). If the API call fails (e.g., the bot has
    never interacted with the user or lacks permissions), it falls back to
    the 'tg://user?id=' deep link format.

    Args:
        bot (Bot): The Telegram Bot instance to perform the API request.
        tg_user_id (int): The unique Telegram user identifier.

    Returns:
        str: A string containing either an 'https://t.me...' public URL
            or a 'tg://user?id=...' deep link.
    """
    try:
        member = await bot.get_chat_member(chat_id=tg_user_id, user_id=tg_user_id)
    except TelegramAPIError:
        return f"tg://user?id={tg_user_id}"
    return member.user.url


async def get_bot_mention(bot: Bot) -> str:
    """
    Retrieves the bot's username formatted as a mention.

    The function first checks the global configuration for a cached mention.
    If not found, it fetches the bot's information from Telegram API,
    updates the cache, and returns the formatted string.

    Args:
        bot (Bot): The Telegram Bot instance to fetch information from.

    Returns:
        str: The bot's username prefixed with '@' (e.g., "@my_audio_bot").
    """
    if config.BOT_MENTION:
        return config.BOT_MENTION

    me = await bot.get_me()
    config.BOT_MENTION = f"@{me.username}"
    return config.BOT_MENTION


async def download_file_to_buffer(bot: Bot, file_id: str) -> io.BytesIO:
    """
    Downloads a file from Telegram servers into an in-memory buffer.

    Args:
        bot (Bot): The Telegram Bot instance to perform the download.
        file_id (str): The unique identifier of the file to be downloaded.

    Returns:
        io.BytesIO: A binary stream containing the downloaded file data,
            with the stream position reset to the beginning (seek=0).
    """
    buffer = io.BytesIO()
    await bot.download(file=file_id, destination=buffer, seek=True)
    return buffer


async def get_caption_mention(bot: Bot, text: str | None = None) -> str:
    """
    Generates a formatted caption string containing a bot mention.

    Args:
        bot (Bot): The Telegram Bot instance used to retrieve the bot's username.
        text (str | None): The prefix text before the mention.
            Defaults to "Slowed by " if None is provided.

    Returns:
        str: A combined string of the prefix text and the bot's username
            (e.g., "Slowed by @YourBot").
    """
    if not text:
        text = "Slowed by "
    mention = await get_bot_mention(bot)
    return f"{text} {mention}"


async def get_filename_mention(bot: Bot, filename: str) -> str:
    """
    Generates a branded filename with '.mp3' extension by appending the bot's mention.

    Args:
        bot (Bot): The Telegram Bot instance used to retrieve the mention.
        filename (str): The original filename or path to process.

    Returns:
        str: A formatted string suitable for a file name
            (e.g., "track_name @my_bot.mp3").

    """
    mention = await get_bot_mention(bot)
    return f"{Path(filename).stem} {mention}.mp3"


async def reply_audio(audio: types.InputFileUnion, message: types.Message, *, effect: bool = True) -> types.Message:
    """
    Sends the audio file as a reply to the original message.

    This function extracts metadata from the original audio, applies an optional
    visual message effect, and includes a mention in the caption.

    Args:
        audio (types.InputFileUnion): The audio file to be sent
            (Buffer, File ID, or URL).
        message (types.Message): The original message containing the source audio
            and context.
        effect (bool): If True, applies a specific Telegram message effect
            (e.g., the 'flame' or 'heart' effect). Defaults to True.

    Returns:
        types.Message: The message object sent by the bot.

    Raises:
        ValueError: If the message does not contain a bot instance
            or an audio object.
    """
    if not message.bot or not message.audio:  # hello fucking Optional
        raise MissingRequiredError

    return await message.reply_audio(
        audio=audio,
        message_effect_id=REPLY_AUDIO_FX if effect else None,
        title=f"{message.audio.title} (Slowed)",
        performer=message.audio.performer,
        caption=await get_caption_mention(message.bot),
    )


@asynccontextmanager
async def temp_message(
    text: str,
    message: types.Message,
    *,
    reply: bool = True,
    please_wait: bool = True,
) -> AsyncGenerator[types.Message]:
    """
    Asynchronous context manager that creates a temporary service message.

    Sends a message at the start and guarantees its deletion upon exiting the context,
    even if an exception occurs during processing.

    Args:
        text (str): The text content of the temporary message.
        message (types.Message): The user message to reply to.
        reply (bool): If True, the service message will reply to the user's message.
        please_wait (bool): If True, attaches a "Please wait" keyboard markup.

    Yields:
        types.Message: The sent service message instance.
    """
    msg = await message.answer(
        text,
        reply_to_message_id=message.message_id if reply else None,
        reply_markup=please_wait_button() if please_wait else None,
    )
    try:
        yield msg
    finally:
        try:
            await msg.delete()
        except TelegramAPIError as err:
            logger.warning(f"Failed to delete temporary message: {err}")


def get_audio_file_extension(audio: types.Audio) -> str:
    """
    Extracts the audio file extension from file_name or mime_type,
    defaults to 'mp3' if no data is available.

    Args:
        audio (str): The Audio object.

    Returns:
        str: The audio file extension without `dot`.
    """
    if audio.file_name and (ext := Path(audio.file_name).suffix.lstrip(".").lower()):
        return ext
    if audio.mime_type:
        return audio.mime_type.split("/")[-1].replace("mpeg", "mp3").replace("x-", "")
    return "mp3"


async def answer_from_update(obj: types.TelegramObject, text: str, *, is_reply: bool = False) -> None:
    """
    Universal responder for different types of Telegram updates.

    Depending on the input object type, it either sends a message to the chat
    or answers a callback query with an alert. This is useful for unified
    error handling or status notifications across various handlers.

    Args:
        obj (types.TelegramObject): The incoming update, typically a
            Message or a CallbackQuery.
        text (str): The response text to be displayed to the user.
        is_reply (bool): Relevant only for Messages. If True, sends the
            response as a reply to the original message. Defaults to False.

    Returns:
        None

    Note:
        For CallbackQuery, 'show_alert=True' is used, which displays
        a modal popup instead of a top-bar notification.
    """
    if isinstance(obj, types.Message):
        await obj.answer(text, reply_to_message_id=obj.message_id if is_reply else None)
    elif isinstance(obj, types.CallbackQuery):
        await obj.answer(text, show_alert=True)
