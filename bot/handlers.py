import os

from aiogram import Dispatcher, types
from aiogram.utils.exceptions import Throttled

from bot import db
from bot.config import AppConfig
from bot.utils import audio
from bot.utils.logger import get_logger

log = get_logger()
config = AppConfig()


def register_handlers(dp: Dispatcher):
    """Register all the Bot's handlers."""

    log.info("Register Bot handlers...")
    dp.register_message_handler(command_start, commands=["start"])
    dp.register_message_handler(command_random, commands=["random"])
    dp.register_message_handler(
        proceed_audio,
        content_types=[types.ContentType.AUDIO],
    )
    dp.register_message_handler(answer_message)


async def proceed_audio(message: types.Message):
    """Slow down uploaded audio track and send it to user."""

    dp = Dispatcher.get_current()
    # Execute throttling manager
    try:
        await dp.throttle('proceed_audio', rate=15)
    except Throttled:
        log.debug(
            "Throttled by user %s with file_id=%s",
            message.from_user.id,
            message.audio.file_id,
        )
        await message.answer('Too many requests! Calm bro!')
        return

    # Check if audio is already slowed then return it from telegram servers
    from_db = await db.get_match(message.audio.file_unique_id)
    if from_db:
        await message.answer(
            "Delivery from past...",
            disable_notification=True,
        )
        await message.answer_audio(
            from_db[2],
            # caption="@slowtunesbot",
        )
        return

    await message.answer(
        "Start recording at 33 rpm for you...",
        disable_notification=True,
    )

    temp_file = os.path.join(
        config.DATA_DIR, f'{message.audio.file_unique_id}.bin'
    )
    await types.ChatActions.record_audio()
    # await message.audio.download(destination_file=temp_file)

    downloaded = await message.audio.download(destination_dir=config.DATA_DIR)

    try:
        slowed_down = await audio.slow_down(downloaded.name, config.SPEED_RATIO)

        tags = {
            'performer': message.audio.to_python().get('performer'),
            'title': " ".join([message.audio.title, "@slowtunesbot"]),
            # 'thumb': types.InputFile(os.path.join(config.DATA_DIR, 'thumb.jpg')),
        }

        if slowed_down:
            await types.ChatActions.upload_audio()
            new_file_name = f'{os.path.splitext(message.audio.file_name)[0]} @slowtunesbot.mp3'  # TODO: refactor
            answer = await message.answer_audio(
                types.InputFile(slowed_down, filename=new_file_name),
                # caption="@slowtunesbot",
                **tags,
            )
            os.remove(slowed_down)
            await db.insert_match(
                message.audio.file_unique_id,
                answer.audio.file_id,
            )
            return
    except Exception as error:
        log.error(error)
    finally:
        downloaded.close()
        os.remove(downloaded.name)

    await types.ChatActions.typing()
    await message.reply('Sorry!')


async def answer_message(message: types.Message):
    """Handler for debug incoming messages."""

    await message.answer("Throw an audio. I'll catch!")


async def command_random(message: types.Message):
    """Handler for `/random` command. Returns random tune from database."""

    random = await db.get_random_match()
    if random:
        await message.answer("Some slow tune for you...")
        await message.answer_audio(random[0], caption="@slowtunesbot")
        return

    log.info("No tunes in database for /random command")
    await message.answer("Sorry, but I don't have tunes yet.")


async def command_start(message: types.Message):
    """Handler for `/start` command."""

    log.info(
        "User join: %s <%s>", message.from_user.id, message.from_user.username
    )
    await message.answer("Send me the audio track " "and i will...")
