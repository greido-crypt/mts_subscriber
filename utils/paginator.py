import math
from typing import List

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Keys, Accounts


class Paginator:
    def __init__(self,
                 items: List,
                 name_of_paginator: str = None,
                 page_now=0,
                 per_page=10):
        self.items = items
        self.per_page = per_page
        self.page_now = page_now
        self.name_paginator = name_of_paginator

    def _generate_page(self):
        ...

    def __str__(self):
        ...


class HistoryPaginator(Paginator):
    def __init__(self, items: List[Keys], page_now=1, per_page=5):
        super().__init__(items=items,
                         page_now=page_now,
                         per_page=per_page,
                         name_of_paginator='history_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        self.items: List[Keys]
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for key_data in self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            key_text = f'✅ {key_data.coupon}' if key_data.account_id else f'❌ {key_data.coupon}'
            page_kb.row(InlineKeyboardButton(text=key_text,
                                             callback_data=f'{self.name_paginator}:look:{key_data.id}'))

        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(self.items.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='🔽 Вернуться в личный кабинет',
                                         callback_data='back_to_personal_area'))

        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return ('<b>🔴 Список ваших активаций:\n'
                '✅ - ключ использован\n'
                '❌ - ключ не использован</b>')


class AccountPaginator(Paginator):
    def __init__(self, items: List, page_now=1, per_page=4):
        super().__init__(items=items,
                         page_now=page_now,
                         per_page=per_page,
                         name_of_paginator='account_paginator')

    def _generate_page(self) -> InlineKeyboardMarkup:
        self.items: List[Accounts]
        page_kb = InlineKeyboardBuilder()

        if self.page_now <= 0:
            self.page_now = 1

        if not bool(len(self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page])):
            self.page_now = 1

        for key_data in self.items[(self.page_now - 1) * self.per_page:self.page_now * self.per_page]:
            page_kb.row(InlineKeyboardButton(text=f'🔍 {key_data.phone_number}',
                                             callback_data=f'get_account:{key_data.id}'))

        page_kb.row(InlineKeyboardButton(text='◀️ Назад',
                                         callback_data=f'{self.name_paginator}:page_prev:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text=f'{self.page_now}/{math.ceil(self.items.__len__() / self.per_page)}',
                                         callback_data=f'{self.name_paginator}:page_now:{self.page_now}'))
        page_kb.add(InlineKeyboardButton(text='Вперед ▶️',
                                         callback_data=f'{self.name_paginator}:page_next:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='✏️ Добавить аккаунт',
                                         callback_data=f'{self.name_paginator}:add_your_account:{self.page_now}'))
        page_kb.row(InlineKeyboardButton(text='↪️ Вернуться в личный кабинет',
                                         callback_data='back_to_personal_area'))
        return page_kb.as_markup()

    def generate_next_page(self) -> InlineKeyboardMarkup:
        self.page_now += 1
        return self._generate_page()

    def generate_prev_page(self) -> InlineKeyboardMarkup:
        self.page_now -= 1
        return self._generate_page()

    def generate_now_page(self) -> InlineKeyboardMarkup:
        return self._generate_page()

    def __str__(self):
        return '<b>🔴 Список ваших аккаунтов:</b>'

    @staticmethod
    def add_account_text():
        return ('<b>🔴 Пришлите номер телефона 📱:\n'
                'Пример: <code>79851215454</code></b>')
