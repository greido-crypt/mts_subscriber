from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage

from settings import BOT_LOGGER, BOTS_TOKENS


class InputUser(StatesGroup):
    phone_number = State()
    key = State()
    sms_code = State()


class InputAdmin(StatesGroup):
    count_keys = State()
    key = State()
    tg_id = State()


bots_list = [Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='html')) for BOT_TOKEN in BOTS_TOKENS]
logger_bot = Bot(token=BOT_LOGGER, default=DefaultBotProperties(parse_mode='html'))
dp = Dispatcher(storage=MemoryStorage())



