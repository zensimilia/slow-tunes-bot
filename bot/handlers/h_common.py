from aiogram import types


async def answer_message(message: types.Message):
    """Handler for other incoming messages."""

    await message.answer(
        "Send me an <code>MP3</code> audio file..."
        "\n\n/help for a list of all commands."
        "\n/random to get and listen some public tunes.",
        disable_notification=True,
    )
