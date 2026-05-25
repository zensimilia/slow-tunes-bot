from aiogram import Dispatcher, F, Router, flags, types
from aiogram.filters import Command

from bot import messages as txt
from bot.core.exceptions import MissingRequiredError
from bot.keyboards.fx import FxAnalogAction, FxAnalogCbd, FxFilterAction, FxFilterCbd, FxReverbAction, FxReverbCbd
from bot.middlewares.auth import invalidate_user_cache
from models.user import User

fx_router = Router()


@fx_router.message(Command("fx"))
@flags.rate_limit(rate=3, key="fx")
async def command_fx(message: types.Message) -> None:
    await message.answer(txt.FX_LIST)


@fx_router.message(Command("analog"))
@flags.rate_limit(rate=3, key="fx_analog")
async def command_analog(message: types.Message, user: User) -> None:
    cbd = FxAnalogCbd(action=FxAnalogAction.LIST)
    options = user.get_options()
    await message.answer(
        txt.FX_ANALOG,
        reply_markup=cbd.get_keyboard(current=options.fx_analog),
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
    options = user.get_options().model_copy(update={"fx_analog": callback_data.value})
    await User.update({User.options: options.model_dump()}).where(User.pk == user.pk)
    await invalidate_user_cache(dispatcher)
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard(callback_data.value))
    await callback.answer(f"Analog fx {callback_data.value} selected", show_alert=False)


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.BACK))
@flags.rate_limit(rate=1, key="fx_analog_back")
async def fx_analog_back(callback: types.CallbackQuery) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.delete()


@fx_router.message(Command("reverb"))
@flags.rate_limit(rate=3, key="fx_reverb")
async def command_reverb(message: types.Message, user: User) -> None:
    cbd = FxReverbCbd(action=FxReverbAction.LIST)
    options = user.get_options()
    await message.answer(
        txt.FX_REVERB,
        reply_markup=cbd.get_keyboard(current=options.fx_reverb),
    )


@fx_router.callback_query(FxReverbCbd.filter(F.action == FxReverbAction.SELECT))
@flags.rate_limit(rate=1, key="fx_reverb_select")
async def fx_reverb_select(
    callback: types.CallbackQuery,
    callback_data: FxReverbCbd,
    user: User,
    dispatcher: Dispatcher,
) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    options = user.get_options().model_copy(update={"fx_reverb": callback_data.value})
    await User.update({User.options: options.model_dump()}).where(User.pk == user.pk)
    await invalidate_user_cache(dispatcher)
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard(callback_data.value))
    await callback.answer(f"Reverb fx {callback_data.value} selected", show_alert=False)


@fx_router.callback_query(FxReverbCbd.filter(F.action == FxReverbAction.BACK))
@flags.rate_limit(rate=1, key="fx_reverb_back")
async def fx_reverb_back(callback: types.CallbackQuery) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.delete()


@fx_router.message(Command("filter"))
@flags.rate_limit(rate=3, key="fx_filter")
async def command_filter(message: types.Message, user: User) -> None:
    cbd = FxFilterCbd(action=FxFilterAction.LIST)
    options = user.get_options()
    await message.answer(
        txt.FX_FILTER,
        reply_markup=cbd.get_keyboard(current=options.fx_filter),
    )


@fx_router.callback_query(FxFilterCbd.filter(F.action == FxFilterAction.SELECT))
@flags.rate_limit(rate=1, key="fx_filter_select")
async def fx_filter_select(
    callback: types.CallbackQuery,
    callback_data: FxFilterCbd,
    user: User,
    dispatcher: Dispatcher,
) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    options = user.get_options().model_copy(update={"fx_filter": callback_data.value})
    await User.update({User.options: options.model_dump()}).where(User.pk == user.pk)
    await invalidate_user_cache(dispatcher)
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard(callback_data.value))
    await callback.answer(f"Reverb fx {callback_data.value} selected", show_alert=False)


@fx_router.callback_query(FxFilterCbd.filter(F.action == FxFilterAction.BACK))
@flags.rate_limit(rate=1, key="fx_filter_back")
async def fx_filter_back(callback: types.CallbackQuery) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.delete()
