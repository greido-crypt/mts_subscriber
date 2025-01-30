from aiogram import Dispatcher

from .admin import admin_router
from .user.main_menu import keyboard_router
from .user.account import account_router
from .user.profile import account_paginator_router, history_paginator_router


def register_user_commands(dp: Dispatcher):
    dp.include_router(admin_router)
    dp.include_router(account_router)
    dp.include_router(account_paginator_router)
    dp.include_router(history_paginator_router)
    dp.include_router(keyboard_router)
