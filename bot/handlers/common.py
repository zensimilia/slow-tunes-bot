from aiogram import types


async def answer_message(message: types.Message):
    """Handler for debug incoming messages."""

    await message.answer(
        "<b>Welcome! Send me audio...</b>"
        "\n\n/help for a list of all commands."
        "\n/random to get and listen shared tunes.",
        disable_notification=True,
    )
