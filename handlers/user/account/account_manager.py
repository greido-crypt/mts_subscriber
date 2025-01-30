import asyncio
import io
import json
import traceback
import uuid

import aiohttp
from aiogram import Router, Bot, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery, Message, BufferedInputFile

from api.ipify.requests import IpifyAPI
from api.mts import MtsAPI
from api.mts.models import AuthModel, TariffList
from api.sms_activate.sms_service import SmsActivateService
from data.keyboard import generate_account_kb, generate_export_cookies_menu, generate_back_to_account_kb, \
    generate_cancel_kb, generate_delete_account_kb, generate_accept_delete_all_subscriptions
from db.models import Accounts, Keys
from db.repository import cookies_repository, accounts_repository, keys_repository
from handlers.user.main_menu import personal_area
from loader import InputUser, logger_bot
from settings import ALLOWED_SUBSCRIPTIONS, SMS_API_KEY, CHANNEL_ID

account_router = Router(name='account_router')


@account_router.callback_query(F.data.startswith(('add_subscribe',
                                                  'disable_subscribe',
                                                  'get_cookies',
                                                  'remove_acc',
                                                  'accept_remove_acc',
                                                  'accept_delete_all_subscriptions')), any_state)
async def read_handlers_in_account(call: CallbackQuery, state: FSMContext, bot: Bot):
    list_call_data = call.data.split(':')
    method = list_call_data[0]
    _id = int(list_call_data[1])
    account_id = int(list_call_data[1])
    async with aiohttp.ClientSession() as session:
        account_data = await accounts_repository.get_account_by_id(account_id=account_id)
        mts_api = MtsAPI(session=session, ya_token=account_data.ya_token)
        mts_api.import_cookies(account_data.cookies)
        ipify_api = IpifyAPI(session=session)
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)
        try:
            mts_api.import_cookies(cookies_list=cookies_data.cookies)
        except KeyError:
            return await call.message.answer(
                '<b>❌ Произошла ошибка при обработке меню аккаунта, отпишите в тех поддержку</b>')

        my_tariff_list = await mts_api.get_tariff_now(phone_number=account_data.phone_number)

        if method == 'get_cookies':
            export_kb, export_kb_text, export_cookies = generate_export_cookies_menu(account_data=account_data,
                                                                                     mts_api=mts_api)
            try:
                return await call.message.edit_text(text=export_kb_text + f'<code>{export_cookies}</code>',
                                                    reply_markup=export_kb.as_markup())
            except TelegramBadRequest:
                file_stream = io.BytesIO(export_cookies.encode('utf-8'))
                file_stream.seek(0)
                file_name = f'{account_data.phone_number}.json'
                input_file = BufferedInputFile(file_stream.read(), filename=file_name)
                await call.message.delete()
                return await call.message.answer_document(caption=export_kb_text,
                                                          document=input_file,
                                                          reply_markup=export_kb.as_markup())

        elif method == 'accept_delete_all_subscriptions':
            response = await mts_api.delete_all_subscriptions()
            if response.status_code != 500:
                await mts_api.premium_authorize()
                cookies = json.loads(mts_api.export_cookies(skip_ip_cookies=True))
                await accounts_repository.update_account_full_data(account_id=account_data.id,
                                                                   cookies=cookies,
                                                                   ya_token=account_data.ya_token)
                response = await mts_api.delete_all_subscriptions()

            if response.status_code == 500:
                await logger_bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=f"<b>❌ Удалены все подписки:\n"
                         f"🔑 Telegram ID: <code>{call.from_user.id}</code>\n"
                         f"👤 Username: @{call.from_user.username}\n"
                         f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>")

            elif response.status_code == 401:
                return await call.message.edit_text(
                    '<b>❌ Истекло время сессии аккаунта, удалите его и авторизируйтесь заново</b>',
                    reply_markup=generate_back_to_account_kb(account_id=account_id))

            return await get_account_data(call=call)

        elif method == 'disable_subscribe':
            kb_delete_all_subscriptions_text, kb_delete_all_subscriptions = generate_accept_delete_all_subscriptions(
                account_data=account_data)
            return await call.message.edit_text(kb_delete_all_subscriptions_text,
                                                reply_markup=kb_delete_all_subscriptions)

        elif method == 'add_subscribe':
            for tariff in my_tariff_list.root:
                if tariff.isPremiumSubscriber:
                    return await call.message.edit_text('<b>❌ У вас уже имеется активная подписка</b>',
                                                        reply_markup=generate_back_to_account_kb(account_id=account_id))
            await call.message.edit_text('<b>✏️ Введите купленный вами ключ:</b>', reply_markup=generate_cancel_kb())
            await state.set_state(InputUser.key)
            return await state.update_data(account_data=account_data, call=call)

        elif method == 'remove_acc':
            kb_delete_to_acc_text, kb_delete_to_acc = generate_delete_account_kb(account_data=account_data)
            return await call.message.edit_text(kb_delete_to_acc_text, reply_markup=kb_delete_to_acc)

        elif method == 'accept_remove_acc':
            await accounts_repository.update_account_data(account_id=account_id)
            await call.message.edit_text('<b>✅ Аккаунт был успешно удалён</b>')
            await logger_bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"<b>❌ Удален аккаунт:\n"
                     f"🔑 Telegram ID: <code>{call.from_user.id}</code>\n"
                     f"👤 Username: @{call.from_user.username}\n"
                     f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>")
            return await personal_area(event=call)


@account_router.message(InputUser.key)
async def account_message_handler(message: Message, state: FSMContext):
    state_data = await state.get_data()

    try:
        account_data: Accounts = state_data['account_data']
        cancel_message: CallbackQuery = state_data['call']
    except KeyError:
        return await message.answer("<b>❌ Ошибка при получении данных для подключения подписки</b>")

    await cancel_message.message.edit_reply_markup()
    await state.clear()

    coupon = message.text
    key_data = await keys_repository.get_coupon_data_by_coupon(coupon=coupon)

    if not key_data:
        return await message.answer(
            '<b>❌ Такой ключ отсутствует в базе</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )

    if key_data.account_id:
        return await message.answer(
            '<b>❌ Ключ уже использован</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )

    if key_data.user_id and key_data.user_id != message.from_user.id:
        return await message.answer(
            '<b>❌ Ключ активирован другим пользователем</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )

    if not key_data.user_id:
        await keys_repository.update_coupon_user_id(coupon_id=key_data.id, user_id=message.from_user.id)
        await logger_bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"<b>✅ Активирован ключ <code>{coupon}</code>:\n"
                 f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                 f"👤 Username: @{message.from_user.username}\n"
                 f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
        )

    await keys_repository.update_coupon_account_id(coupon_id=key_data.id, account_id=account_data.id)

    subscription_answers = {
        0: '<b>Происходит подключение подписки, ожидайте 5 минут...\nТариф: <i>навсегда (без гб)</i></b>',
        1: '<b>Происходит подключение подписки, ожидайте 5 минут...\nТариф: <i>месячный (гб)</i></b>',
        2: '<b>Происходит подключение подписки, ожидайте 5 минут...\nТариф: <i>на год (гб)</i></b>',
    }

    async with aiohttp.ClientSession() as session:
        account_data = await accounts_repository.get_account_by_id(account_id=account_data.id)
        mts_api = MtsAPI(session=session, ya_token=account_data.ya_token)
        mts_api.import_cookies(account_data.cookies)

        ipify_api = IpifyAPI(session=session)
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)

        try:
            mts_api.import_cookies(cookies_list=cookies_data.cookies)
        except KeyError:
            return await message.reply(
                '<b>❌ Произошла ошибка при обработке меню аккаунта, отпишите в тех поддержку</b>')

        tariff_list = await mts_api.get_tariff_list(phone_number=account_data.phone_number)

        await message.reply(subscription_answers[key_data.subscription_id])

        if key_data.subscription_id == 0 or key_data.subscription_id == 2:
            await handle_subscription(message, key_data, tariff_list, mts_api, account_data)

        elif key_data.subscription_id == 1:
            await handle_monthly_subscription(message, key_data, mts_api, ipify_api, session, account_data)


async def handle_subscription(message: Message,
                              key_data: Keys,
                              tariff_list: TariffList,
                              mts_api: MtsAPI,
                              account_data: Accounts):
    for tariff in tariff_list.root:
        if ALLOWED_SUBSCRIPTIONS[key_data.subscription_id] == tariff.contentId:
            break
    else:
        await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
        return await message.reply(
            '<b>❌ Произошла ошибка при подключении подписки: <i>нет доступного тарифа</i>\n'
            '🔴 Для того, чтобы подключить подписку - отключите все активные подписки на номере телефона\n'
            '🔴 Использование ключа было сброшено, для повторной попытки активации премиума - введите ключ заново</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )

    try:
        response = await mts_api.activate_mts_premium(
            phone_number=account_data.phone_number,
            content_id=ALLOWED_SUBSCRIPTIONS[key_data.subscription_id]
        )

        if response.subscriptionId:
            await logger_bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"<b>✅ Подключена подписка №{key_data.subscription_id}:\n"
                     f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                     f"👤 Username: @{message.from_user.username}\n"
                     f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
            )
            return await message.reply(
                '<b>✅ Подписка успешно подключена!</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id)
            )
        else:
            await logger_bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"<b>❌ Произошла ошибка при подключении подписки №{key_data.subscription_id}:\n"
                     f"🚫 Ошибка: {response.model_dump(mode='json')}\n"
                     f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                     f"👤 Username: @{message.from_user.username}\n"
                     f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
            )
            await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
            return await message.reply(
                '<b>❌ Произошла ошибка при подключении подписки\n'
                '🔴 Использование ключа было сброшено, для повторной попытки активации премиума - введите ключ заново</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id)
            )


    except Exception as e:
        await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
        await logger_bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"<b>❌ Произошла ошибка при подключении подписки №{key_data.subscription_id}:\n"
                 f"🚫 Ошибка: {e}\n"
                 f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                 f"👤 Username: @{message.from_user.username}\n"
                 f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
        )
        return await message.reply(
            '<b>❌ Произошла ошибка при подключении подписки'
            '🔴 Использование ключа было сброшено, для повторной попытки активации премиума - введите ключ заново</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )


async def handle_monthly_subscription(message: Message,
                                      key_data: Keys,
                                      mts_api: MtsAPI,
                                      ipify_api: IpifyAPI,
                                      session: aiohttp.ClientSession,
                                      account_data: Accounts,
                                      try_subscription=0):
    if try_subscription > 5:
        await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
        await logger_bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"<b>❌ Произошла ошибка при подключении подписки №{key_data.subscription_id}:\n"
                 f"🚫 Ошибка: не смог активировать подписку более 5 раз\n"
                 f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                 f"👤 Username: @{message.from_user.username}\n"
                 f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
        )
        return await message.reply(
            '<b>❌ Произошла ошибка при подключении подписки на нашей стороне\n'
            '🔴 Использование ключа было сброшено, для повторной попытки активации премиума - введите ключ заново</b> в меню аккаунта',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )

    try:
        mts_api.clear_cookies()
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)
        mts_api.import_cookies(cookies_list=cookies_data.cookies)
        sms_service = SmsActivateService(api_key=SMS_API_KEY, session=session)

        response = await sms_service.getNumberV2(service='da', country=0, operator='tele2,yota')

        phone_number = response.phoneNumber
        activation_id = response.activationId
        state_param = mts_api.generate_random_string()

        auth_model: AuthModel = AuthModel(phone_number=phone_number, state=state_param)

        response = await mts_api.mts_premium_auth_first_step(auth_data=auth_model)

        if response.status_code != 200:
            await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
            await logger_bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"<b>❌ Произошла ошибка при подключении подписки №{key_data.subscription_id}:\n"
                     f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                     f"👤 Username: @{message.from_user.username}\n"
                     f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
            )
            return await message.reply(
                '<b>❌ Произошла ошибка при подключении подписки на нашей стороне\n'
                '🔴 Использование ключа было сброшено, для повторной попытки активации премиума - введите ключ заново</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id)
            )

        json_data = json.loads(response.text)

        sms_code_data = await sms_service.get_sms_code(id=activation_id, time_out=0.5)
        auth_model.sms_code = sms_code_data.sms_code
        response = await mts_api.mts_premium_auth_second_step(auth_data=auth_model, data=json_data)
        json_data = json.loads(response.text)
        success_url = json_data.get('successUrl')
        if not success_url:
            await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
            return await message.reply(
                '<b>❌ Произошла ошибка при подключении подписки\n'
                '🔴 Использование ключа было сброшено, можете им воспользоваться ещё раз</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id)
            )

        await mts_api.premium_authorize()

        ya_token = await mts_api.mts_music_authorize(state=str(uuid.uuid4()))
        json_cookies = mts_api.export_cookies(skip_ip_cookies=True)
        await accounts_repository.add_account(
            phone_number=auth_model.phone_number, cookies=json_cookies,
            ya_token=ya_token
        )
        await mts_api.activate_mts_premium(
            phone_number=phone_number,
            content_id=ALLOWED_SUBSCRIPTIONS[key_data.subscription_id]
        )
        await asyncio.sleep(10)

        response = await mts_api.user_invite(phone_number=account_data.phone_number)
        invite_url = response.link
        if not invite_url:
            return await message.reply(
                '<b>❌ Произошла ошибка при подключении подписки:\n'
                '🔴 Пожалуйста, проверьте наличие возможных ограничений на подключение МТС Премиум на вашем номере.\n'
                '🔴 Для уточнения информации, рекомендуем связаться с поддержкой МТС.\n'
                '🔴 Использование ключа было сброшено, вы можете попробовать его использовать снова.</b>',
                reply_markup=generate_back_to_account_kb(account_id=account_data.id)
            )

        await logger_bot.send_message(
            chat_id=CHANNEL_ID,
            text=f"<b>✅ Подключена подписка №{key_data.subscription_id}:\n"
                 f'<b>✅ Ссылка для подключения подписки: {invite_url}</b>\n'
                 f"🔑 Telegram ID: <code>{message.from_user.id}</code>\n"
                 f"👤 Username: @{message.from_user.username}\n"
                 f"📱 Номер телефона: <code>{account_data.phone_number}</code></b>"
        )
        return await message.reply(
            f'<b>✅ Ссылка для подключения подписки: {invite_url}\n'
            f'🟢 Также приглашение в семью было выслано на ваш личный номер телефона, на который вы хотели подключить подписку\n'
            f'🟢 Ссылка действительна ~1 час</b>',
            reply_markup=generate_back_to_account_kb(account_id=account_data.id)
        )
    except Exception as e:
        await keys_repository.delete_coupon_account_id(coupon_id=key_data.id)
        print(traceback.print_exc())
        # return await handle_monthly_subscription(message, key_data, mts_api, ipify_api, session, account_data,
        #                                          try_subscription + 1)


@account_router.callback_query(F.data.startswith(("get_account")))
async def get_account_data(call: CallbackQuery):
    list_call_data = call.data.split(':')
    _ = list_call_data[0]
    account_id = int(list_call_data[1])
    async with aiohttp.ClientSession() as session:
        account_data = await accounts_repository.get_account_by_id(account_id=account_id)
        if account_data.is_deleted:
            await call.message.answer('<b>❌ Этот аккаунт был удалён с вашего личного кабинета</b>')
            return await personal_area(event=call)

        elif not account_data:
            await call.message.answer('<b>❌ Этот аккаунт не был найден в вашем личном кабинете</b>')
            return await personal_area(event=call)

        mts_api = MtsAPI(session=session, ya_token=account_data.ya_token)
        mts_api.import_cookies(account_data.cookies)
        ipify_api = IpifyAPI(session=session)
        response = await ipify_api.get_ip()
        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)
        try:
            mts_api.import_cookies(cookies_list=cookies_data.cookies)
        except KeyError:
            await call.message.answer(
                '<b>❌ Произошла ошибка при заходе в меню аккаунта, отпишите в тех поддержку</b>')
            return await personal_area(event=call)

        my_tariff_list = await mts_api.get_tariff_now(phone_number=account_data.phone_number)
        allowed_tariff_data = await mts_api.get_tariff_list(phone_number=account_data.phone_number)
        keyboard, text_message = generate_account_kb(account_data=account_data,
                                                     my_tariff_data=my_tariff_list.root,
                                                     allowed_tariff_data=allowed_tariff_data.root)

        try:
            return await call.message.edit_text(text_message, reply_markup=keyboard)

        except TelegramBadRequest:
            await call.message.delete()
            return await call.message.answer(text_message, reply_markup=keyboard)
