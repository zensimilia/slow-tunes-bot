from aiogram.filters.callback_data import CallbackData


class ShareCbd(CallbackData, prefix="share"):
    action: str
    pk: int
    is_private: bool
    is_random: bool
