import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from data.keyboard import generate_admin_kb, generate_new_keys_cd, generate_cancel_kb, generate_generate_new_keys_kb
from db.repository import users_repository, keys_repository
from loader import InputAdmin
from settings import ADMIN_LIST

admin_router = Router()


@admin_router.message(Command('admin'))
async def admin(message: Message):
    if message.from_user.id not in ADMIN_LIST:
        return
    await message.delete()
    admin_keyboard = generate_admin_kb()
    answer_text = '<b>🔴 Вы успешно вошли в панель администратора: ✅\n</b>'
    answer_text += '<b>Список администраторов на данный момент</b>:\n' + '\b\n'.join(str(admin) for admin in ADMIN_LIST)
    answer_text += f'\n<b>Количество пользователей на данный момент: {(await users_repository.select_all_users()).__len__()}</b>'
    await message.answer(answer_text,
                         reply_markup=admin_keyboard)


@admin_router.callback_query(F.data == generate_new_keys_cd)
async def new_keys_callback(call: CallbackQuery):
    kb_text, kb = generate_generate_new_keys_kb()
    await call.message.edit_text(kb_text, reply_markup=kb)


@admin_router.callback_query(F.data.startswith('generate_keys'))
async def generate_keys_callback(call: CallbackQuery, state: FSMContext):
    _, subscription_id = call.data.split(':')
    await state.update_data(subscription_id=subscription_id)
    await state.set_state(InputAdmin.count_keys)
    return await call.message.answer('<b>🔴 Введите количество ключей:</b>')


@admin_router.message(InputAdmin.count_keys)
async def generate_new_keys(message: Message, state: FSMContext):
    state_data = await state.get_data()
    call: CallbackQuery = state_data.get('call')
    subscription_id: int = int(state_data.get('subscription_id', '0'))
    if call:
        await call.message.edit_reply_markup()
    if not message.text.isdigit():
        return await message.reply('<b>🔴 Введите <u>правильно</u> количество нужных ключей</b>')
    count_keys = int(message.text)
    keys = []
    for test in range(count_keys):
        coupon = uuid.uuid4().hex
        keys.append(coupon)
    await keys_repository.add_codes(coupons=keys, subscription_id=subscription_id)
    await message.answer(f'<b>🔴 Ваши ключи №{subscription_id}:</b>\n' + '\n'.join(f'<code>{key}</code>' for key in keys))
    await state.clear()
