import asyncio
import time
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from db.repository import users_repository
from loader import logger_bot
from settings import CHANNEL_ID, MESSAGE_SPAM_TIMING


class MessageMiddleware(BaseMiddleware):
    def __init__(self):
        self.storage = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]
    ) -> Any:

        user_data = await users_repository.get_user_by_tg_id(user_id=event.from_user.id)

        if not user_data:
            await users_repository.add_user(user_id=event.from_user.id, username=event.from_user.username)
            await logger_bot.send_message(
                chat_id=CHANNEL_ID,
                text=f"<b>❤️ Зарегистрирован новый пользователь:\n"
                     f"🔑 Telegram ID: <code>{event.from_user.id}</code>\n"
                     f"👤 Username: @{event.from_user.username}</b>")

        if await self.throttling(event):
            return

        return await handler(event, data)

    async def throttling(self, event: Message):
        user_id = f'{event.from_user.id}'
        check_user = self.storage.get(user_id)
        if check_user:

            if check_user['spam_block']:
                return True

            if time.time() - check_user['timestamp'] <= int(MESSAGE_SPAM_TIMING):
                self.storage[user_id]['timestamp'] = time.time()
                self.storage[user_id]['spam_block'] = True
                await event.answer(f'<b>❌ Обнаружена подозрительная активность.</b>')
                await asyncio.sleep(int(MESSAGE_SPAM_TIMING))
                self.storage[user_id]['spam_block'] = False
                return True

        self.storage[user_id] = {'timestamp': time.time(), 'spam_block': False}
        return False

