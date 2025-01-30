from aiogram import F, Router
from aiogram.fsm.state import any_state
from aiogram.types import CallbackQuery

from db.repository import keys_repository
from utils.paginator import HistoryPaginator

history_paginator_router = Router()


@history_paginator_router.callback_query(F.data.contains(('look')), any_state)
async def look_callback_query(call: CallbackQuery):
    """
        paginator, method, page_now or account_id
        """
    _, method, coupon_id = call.data.split(":")
    acc_data = await keys_repository.get_coupon_data_by_id(coupon_id=int(coupon_id))
    return await call.answer(f'Дата создания ключа: {acc_data.creation_date.strftime("%d/%m/%Y")}\n'
                             f'Номер телефона: {acc_data.account.phone_number}', show_alert=True)


@history_paginator_router.callback_query(F.data.startswith(('history_paginator')), any_state)
async def send_history_menu(call: CallbackQuery):
    tg_user_id = call.from_user.id
    list_of_purchases = await keys_repository.get_coupons_by_user_id(user_id=tg_user_id)
    """
    paginator, method, page_now or item_id
    """
    _, method, page_now = call.data.split(":")
    history_paginator = HistoryPaginator(items=list_of_purchases, page_now=int(page_now))
    if not bool(len(list_of_purchases)):
        return await call.answer('Список активаций пуст :(\n'
                                 'Давай исправим это ?', show_alert=True)
    elif method == 'page_next':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_next_page())
    elif method == 'page_now':
        return await call.answer(f'Вы находитесь на странице: {page_now}', show_alert=True)
    elif method == 'page_prev':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_prev_page())
    elif method == 'send_menu':
        return await call.message.edit_text(text=history_paginator.__str__(),
                                            reply_markup=history_paginator.generate_now_page())
