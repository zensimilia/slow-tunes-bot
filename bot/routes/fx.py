from typing import TYPE_CHECKING

from aiogram import Bot, F, Router, flags, types
from aiogram.filters import Command

from bot import messages as txt
from bot.core.exceptions import MissingRequiredError
from bot.keyboards.fx import FxAnalog, FxAnalogAction, FxAnalogCbd

if TYPE_CHECKING:
    from db.models import User
    from db.repository.master import MasterStorage


fx_router = Router()


@fx_router.message(Command("fx"))
@flags.rate_limit(rate=10, key="fx")
async def command_fx(message: types.Message) -> None:
    await message.answer("List of available effects:\n\n/analog - bla-bla-bla")


@fx_router.message(Command("analog"))
@flags.rate_limit(rate=10, key="fx_analog")
async def command_analog(message: types.Message, user: User) -> None:
    cbd = FxAnalogCbd(action=FxAnalogAction.LIST)
    await message.answer("This is analog effects. Choose one:", reply_markup=cbd.get_keyboard())


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.SELECT))
@flags.rate_limit(rate=1, key="fx_analog_select")
async def fx_analog_select(callback: types.CallbackQuery, callback_data: FxAnalogCbd) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard(callback_data.fx))


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.CLEAR))
@flags.rate_limit(rate=1, key="fx_analog_clear")
async def fx_analog_clear(callback: types.CallbackQuery, callback_data: FxAnalogCbd) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.edit_reply_markup(reply_markup=callback_data.get_keyboard())


@fx_router.callback_query(FxAnalogCbd.filter(F.action == FxAnalogAction.BACK))
@flags.rate_limit(rate=1, key="fx_analog_back")
async def fx_analog_back(callback: types.CallbackQuery, _callback_data: FxAnalogCbd) -> None:
    if not isinstance(callback.message, types.Message):
        raise MissingRequiredError
    await callback.message.delete()
