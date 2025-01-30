from typing import List

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from api.mts import MtsAPI
from api.mts.models import MyTariff, Tariff
from db.models import Accounts
from settings import HELP_URL, COOKIES_HELP_URL, ALLOWED_SUBSCRIPTIONS

personal_area_kb_text = 'ℹ️ Личный кабинет'
help_kb_text = 'Помощь ❓'


def generate_start_kb() -> ReplyKeyboardMarkup:
    start_kb = ReplyKeyboardBuilder()
    start_kb.row(KeyboardButton(text=personal_area_kb_text))
    start_kb.row(KeyboardButton(text=help_kb_text))
    return start_kb.as_markup(resize_keyboard=True)


def generate_help_kb() -> InlineKeyboardMarkup:
    help_kb = InlineKeyboardBuilder()
    help_kb.row(InlineKeyboardButton(text='Инструкция',
                                     url=HELP_URL))
    return help_kb.as_markup()


def generate_personal_area_kb() -> InlineKeyboardMarkup:
    personal_area_kb = InlineKeyboardBuilder()
    personal_area_kb.row(
        InlineKeyboardButton(text="📋 История активаций", callback_data="history_paginator:send_menu:1"))
    personal_area_kb.row(InlineKeyboardButton(text="📱 Мои аккаунты", callback_data="account_paginator:send_menu:1"))
    return personal_area_kb.as_markup()


cancel_input_cd = 'cancel_input'


def generate_cancel_kb() -> InlineKeyboardMarkup:
    cancel_input_kb = InlineKeyboardBuilder()
    cancel_input_kb.row(InlineKeyboardButton(text='Отменить ввод ❌',
                                             callback_data=cancel_input_cd))
    return cancel_input_kb.as_markup()


generate_new_keys_text = 'Создать новые ключи'
generate_new_keys_cd = 'generate_new_keys'
get_key_info_text = 'Получить информацию по ключу'
get_key_info_cd = 'get_key_info'
get_user_info_text = 'Получить информацию по пользователю'
get_user_info_cd = 'get_user_info'


def generate_admin_kb() -> InlineKeyboardMarkup:
    admin_kb = InlineKeyboardBuilder()
    admin_kb.row(InlineKeyboardButton(text=generate_new_keys_text,
                                      callback_data=generate_new_keys_cd))
    admin_kb.row(InlineKeyboardButton(text=get_key_info_text,
                                      callback_data=get_key_info_cd))
    admin_kb.row(InlineKeyboardButton(text=get_user_info_text,
                                      callback_data=get_user_info_cd))
    return admin_kb.as_markup()


def generate_generate_new_keys_kb() -> tuple[str, InlineKeyboardMarkup]:
    new_keys_kb_text = '<b>🔴 Меню создания ключей</b>'
    new_keys_kb = InlineKeyboardBuilder()
    for key_id in range(0, 3):
        new_keys_kb.row(InlineKeyboardButton(text=f'🔑 Создать ключи №{key_id}', callback_data=f'generate_keys:{key_id}'))
    return new_keys_kb_text, new_keys_kb.as_markup()


def generate_get_account_kb_by_id(account_id: int | str) -> InlineKeyboardMarkup:
    """
    _id: account id from Account class
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text='↪️ Перейти к аккаунту',
                                      callback_data=f'get_account:{account_id}'))
    return keyboard.as_markup()


def generate_delete_account_kb(account_data: Accounts) -> tuple[str, InlineKeyboardMarkup]:
    kb_delete_to_acc = InlineKeyboardBuilder()
    kb_delete_to_acc_text = '<b>Вы точно хотите удалить аккаунт?</b>'
    kb_delete_to_acc.add(InlineKeyboardButton(text='✅ Подтвердить действие',
                                              callback_data=f'accept_remove_acc:{account_data.id}'))
    kb_delete_to_acc.add(InlineKeyboardButton(text='❌ Отменить действие',
                                              callback_data=f'get_account:{account_data.id}'))
    return kb_delete_to_acc_text, kb_delete_to_acc.as_markup()


def generate_accept_delete_all_subscriptions(account_data: Accounts) -> tuple[str, InlineKeyboardMarkup]:
    kb_delete_all_subscriptions = InlineKeyboardBuilder()
    kb_delete_all_subscriptions_text = '<b>Вы точно хотите удалить подписку?</b>'
    kb_delete_all_subscriptions.add(InlineKeyboardButton(text='✅ Подтвердить действие',
                                                         callback_data=f'accept_delete_all_subscriptions:{account_data.id}'))
    kb_delete_all_subscriptions.add(InlineKeyboardButton(text='❌ Отменить действие',
                                                         callback_data=f'get_account:{account_data.id}'))
    return kb_delete_all_subscriptions_text, kb_delete_all_subscriptions.as_markup()


def generate_back_to_account_kb(account_id: int | str) -> InlineKeyboardMarkup:
    kb_back_to_acc = InlineKeyboardBuilder()
    kb_back_to_acc.add(InlineKeyboardButton(text='↪️ Вернуться в аккаунт',
                                            callback_data=f"get_account:{account_id}"))
    return kb_back_to_acc.as_markup()


def generate_account_kb(account_data: Accounts,
                        my_tariff_data: List[MyTariff],
                        allowed_tariff_data: List[Tariff]
                        ) -> tuple[InlineKeyboardMarkup, str]:
    account_menu = InlineKeyboardBuilder()
    account_text = f'<b>📱 Номер телефона: <code>{account_data.phone_number}</code></b>\n'

    if my_tariff_data:
        account_text += (f'<b>💳 Название тарифа: <i>{my_tariff_data[0].contentName}</i>\n'
                         f'💰 Цена: <i>{my_tariff_data[0].price}</i>\n'
                         f'⭐ Премиум подписчик: <i>{"Да" if my_tariff_data[0].isPremiumSubscriber else "Нет"}</i>\n'
                         f'📅 Дата подписки: <i>{my_tariff_data[0].subscriptionDate}</i></b>')

    if my_tariff_data and my_tariff_data[0].isPremiumSubscriber:
        account_menu.row(InlineKeyboardButton(text='🔴 Отключить подписку', callback_data=f"disable_subscribe:{account_data.id}"))
    else:
        account_menu.row(InlineKeyboardButton(text='🟢 Подключить подписку', callback_data=f"add_subscribe:{account_data.id}"))

    account_menu.row(InlineKeyboardButton(text='🍪 Выгрузить Cookies', callback_data=f"get_cookies:{account_data.id}"))

    account_menu.row(InlineKeyboardButton(text='♻️ Обновить сведения', callback_data=f"get_account:{account_data.id}"))

    account_menu.row(InlineKeyboardButton(text='❌ Удалить аккаунт', callback_data=f'remove_acc:{account_data.id}'))

    account_menu.row(
        InlineKeyboardButton(text='↪️ Назад в список аккаунтов', callback_data=f"account_paginator:send_menu:{1}"))

    return account_menu.as_markup(), account_text


def generate_export_cookies_menu(account_data: Accounts,
                                 mts_api: MtsAPI):
    export_menu = InlineKeyboardBuilder()
    export_cookies = mts_api.export_cookies(skip_ip_cookies=True)
    export_menu_text = (f'<b>📱 Номер телефона: <code>{account_data.phone_number}</code>\n'
                        f'🍪 Экспортированные cookies:\n'
                        f'<a href="{COOKIES_HELP_URL}">Как пользоваться⁉️</a></b>\n')
    export_menu.row(InlineKeyboardButton(text='↪️ Вернуться в аккаунт',
                                         callback_data=f"get_account:{account_data.id}"))
    return export_menu, export_menu_text, export_cookies
