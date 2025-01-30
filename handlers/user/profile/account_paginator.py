import asyncio
import json
import urllib.parse
import uuid

import aiohttp
from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, Message

from api.ipify.requests import IpifyAPI
from api.mts import MtsAPI
from api.mts.models import AuthModel
from data.keyboard import generate_cancel_kb, generate_get_account_kb_by_id
from db.repository import accounts_repository, cookies_repository
from loader import InputUser, logger_bot
from settings import CHANNEL_ID
from utils.is_valid_russian_phone_number import is_valid_russian_phone_number
from utils.paginator import AccountPaginator

account_paginator_router = Router()


@account_paginator_router.callback_query(F.data.startswith(('account_paginator')), any_state)
async def send_accounts_list_menu(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_user_id = call.from_user.id
    accounts_list = await accounts_repository.get_accounts_by_user_id(tg_user_id)
    _, method, page_now = call.data.split(':')
    account_paginator = AccountPaginator(items=accounts_list, page_now=int(page_now))

    if method == 'page_next':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_next_page())

    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)

    elif method == 'page_prev':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_prev_page())

    elif method == 'send_menu':
        return await call.message.edit_text(text=account_paginator.__str__(),
                                            reply_markup=account_paginator.generate_now_page())

    elif method == 'add_your_account':
        await state.set_state(InputUser.phone_number)
        await state.update_data(call=call)
        return await call.message.edit_text(text=account_paginator.add_account_text(),
                                            reply_markup=generate_cancel_kb())


@account_paginator_router.message(InputUser.phone_number)
async def input_phone(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.clear()
    call: CallbackQuery = state_data.get('call')
    await call.message.edit_reply_markup()
    if not is_valid_russian_phone_number(phone_number=message.text):
        return message.reply('<b>❌ Введите правильно номер телефона</b>')
    phone_number = message.text
    async with aiohttp.ClientSession() as session:
        mts_api = MtsAPI(session=session, base_url='https://login.mts.ru')
        ipify_api = IpifyAPI(session=session)
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)
        try:
            mts_api.import_cookies(cookies_list=cookies_data.cookies)
        except KeyError:
            return await message.answer('<b>❌ Произошла ошибка при отправке смс-кода, отпишите в тех поддержку</b>')

        state_param = mts_api.generate_random_string()

        auth_model: AuthModel = AuthModel(phone_number=phone_number, state=state_param)

        response = await mts_api.mts_premium_auth_first_step(auth_data=auth_model)

        if response.status_code != 200:
            await message.answer(f'<b>🔴 Ошибка при отправке смс-кода на номер: {phone_number}</b>')
            await asyncio.sleep(3)
            return await input_phone(message, state)

        json_data = json.loads(response.text)

        cancel_message = await message.answer(f'<b>🔴 Пришлите смс-код, отправленный на номер {phone_number} ✉️:</b>',
                                              reply_markup=generate_cancel_kb())
        await state.update_data(json_data=json_data,
                                auth_model=auth_model,
                                message=cancel_message)
        await state.set_state(InputUser.sms_code)


@account_paginator_router.message(InputUser.sms_code)
async def sms_input(message: Message, state: FSMContext):
    state_data = await state.get_data()
    await state.clear()
    cancel_message: Message = state_data['message']
    await cancel_message.edit_reply_markup()
    json_data: dict = state_data['json_data']
    auth_model: AuthModel = state_data['auth_model']
    auth_model.sms_code = message.text

    async with aiohttp.ClientSession() as session:
        mts_api = MtsAPI(session=session, base_url='https://login.mts.ru')
        ipify_api = IpifyAPI(session=session)
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)
        try:
            mts_api.import_cookies(cookies_list=cookies_data.cookies)
        except KeyError:
            return await message.answer('<b>❌ Произошла ошибка при отправке смс-кода, отпишите в тех поддержку</b>')

        response = await mts_api.mts_premium_auth_second_step(auth_data=auth_model, data=json_data)

        json_data = json.loads(response.text)
        success_url = json_data.get('successUrl')

        if not success_url:
            return await message.answer('<b>❌ Ошибка: введён неверный смс код</b>')

        await mts_api.premium_authorize()

        ya_token = await mts_api.mts_music_authorize(state=str(uuid.uuid4()))

        cookies = mts_api.export_cookies(skip_ip_cookies=True)
        json_cookies = json.loads(cookies)

        all_accounts_data = await accounts_repository.get_accounts_by_user_id(user_id=message.from_user.id) + await accounts_repository.get_accounts_by_user_id(user_id=message.from_user.id, is_deleted=True)

        for account_data in all_accounts_data:
            if account_data.phone_number == auth_model.phone_number:
                await accounts_repository.update_account_full_data(cookies=json_cookies, ya_token=ya_token,
                                                                   account_id=account_data.id)
                break
        else:
            status_account = await accounts_repository.add_account(phone_number=auth_model.phone_number, cookies=json_cookies,
                                                                   ya_token=ya_token, user_id=message.from_user.id)

            if not status_account:
                return await message.answer('<b>❌ Ошибка при добавлении номера в личный кабинет</b>')

        all_accounts_data = await accounts_repository.get_accounts_by_user_id(user_id=message.from_user.id) + await accounts_repository.get_accounts_by_user_id(user_id=message.from_user.id, is_deleted=True)
        for account_data in all_accounts_data:
            if account_data.phone_number == auth_model.phone_number:
                await logger_bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"<b>✅ Номер успешно добавлен в личный кабинет:\n"
                         f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                         f"👤 Username: @{message.from_user.username}\n"
                         f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>")
                return await message.answer(text='<b>✅ Номер успешно добавлен в личный кабинет</b>',
                                            reply_markup=generate_get_account_kb_by_id(account_data.id))
