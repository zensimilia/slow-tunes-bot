import json

from aiogram import Dispatcher, F, Router, flags, types
from aiogram.filters import Command

from bot.core.exceptions import MissingRequiredError
from bot.keyboards.fx import FxAnalogAction, FxAnalogCbd
from bot.middlewares.auth import invalidate_user_cache
from bot.services.ffmpeg import FxAnalog
from models.user import User, UserOptions

fx_router = Router()


@fx_router.message(Command("fx"))
@flags.rate_limit(rate=3, key="fx")
async def command_fx(message: types.Message) -> None:
    await message.answer("List of available effects:\n\n/analog - bla-bla-bla")  # TODO @me: text


@fx_router.message(Command("analog"))
@flags.rate_limit(rate=3, key="fx_analog")
async def command_analog(message: types.Message, user: User) -> None:
    cbd = FxAnalogCbd(action=FxAnalogAction.LIST)
    opts = UserOptions(**json.loads(user.options))
    fx = FxAnalog(opts.fx_analog)
    await message.answer(
        "This is analog effects. Choose one:",  # TODO @me: text
        reply_markup=cbd.get_keyboard(current=fx),
    )


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.SELECT))
@flags.rate_limit(rate=1, key="fx_analog_select")
async def fx_analog_select(
    callback: types.CallbackQuery,
    callback_data: FxAnalogCbd,
    user: User,
    dispatcher: Dispatcher,
) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    opts = UserOptions(fx_analog=callback_data.fx)
    await User.update({User.options: opts}).where(User.pk == user.pk)
    await invalidate_user_cache(dispatcher)
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard(callback_data.fx))
    await callback.answer(f"Analog fx {callback_data.fx} selected", show_alert=False)


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.CLEAR))
@flags.rate_limit(rate=1, key="fx_analog_clear")
async def fx_analog_clear(
    callback: types.CallbackQuery,
    callback_data: FxAnalogCbd,
    user: User,
    dispatcher: Dispatcher,
) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await User.update({User.options: UserOptions(fx_analog=None)}).where(User.pk == user.pk)
    await invalidate_user_cache(dispatcher)
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard())


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.BACK))
@flags.rate_limit(rate=1, key="fx_analog_back")
async def fx_analog_back(callback: types.CallbackQuery) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.delete()
