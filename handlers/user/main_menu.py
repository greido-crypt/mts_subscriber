import random

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import Message, CallbackQuery

from data.keyboard import generate_start_kb, cancel_input_cd, generate_help_kb, generate_personal_area_kb, help_kb_text
from db.repository import users_repository, keys_repository
from settings import STICKER_ID

keyboard_router = Router()


@keyboard_router.message(Command('start'), any_state)
async def echo_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer_sticker(random.choice(STICKER_ID))
    await message.answer(
        '<b>🦔 <u>Добро пожаловать в бота для подключения <i>MTS-PREMIUM!</i></u>🦔 🚀\n'
        'Ознакомься с выпавшей снизу клавиатурой и начни получать удовольствие вместе со '
        'мной! 😊🔴</b>',
        reply_markup=generate_start_kb())


@keyboard_router.callback_query(F.data == 'back_to_personal_area')
@keyboard_router.message(F.text == 'ℹ️ Личный кабинет')
async def personal_area(event: CallbackQuery | Message):
    tg_user_id = event.from_user.id
    all_user_keys = await keys_repository.get_coupons_by_user_id(user_id=tg_user_id)
    number_of_purchases = len(all_user_keys)
    user_data = await users_repository.get_user_by_tg_id(user_id=tg_user_id)
    registration_date = user_data.creation_date.strftime('%Y-%m-%d %H:%M:%S')

    message_text = f'<b>❤️ Пользователь: @{event.from_user.username}\n' \
                   f'🔑 Ваш Id: <code>{tg_user_id}</code>\n' \
                   f'💸 Количество покупок: {number_of_purchases}\n' \
                   f'📋 Дата регистрации: {registration_date}</b>'

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(message_text, reply_markup=generate_personal_area_kb())
    else:
        await event.answer(message_text, reply_markup=generate_personal_area_kb())


@keyboard_router.callback_query(F.data == cancel_input_cd)
async def cancel_callback_query(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(f'<b>🔴 Действие отменено</b>')
    await state.clear()


@keyboard_router.callback_query(F.data == 'help')
async def help_kb(call: CallbackQuery):
    await call.message.edit_text('<b>🔴 Меню помощи:\n'
                                 'По вопросам обращаться в поддержку магазина</b>', reply_markup=generate_help_kb())


@keyboard_router.message(F.text == help_kb_text, any_state)
async def help_kb(message: Message):
    await message.answer('<b>🔴 Меню помощи:\n'
                         'По вопросам обращаться в поддержку магазина</b>', reply_markup=generate_help_kb())


@keyboard_router.callback_query()
async def callback_query(call: CallbackQuery):
    await call.message.edit_text('<b>🔴 Я не понимаю вас..</b>')


@keyboard_router.message()
async def echo(message: Message):
    await message.answer('<b>🔴 Я не понимаю вас..</b>', reply_markup=generate_start_kb())
