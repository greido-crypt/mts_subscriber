import asyncio
from operator import attrgetter
import aiohttp
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from anyio import to_thread
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from webdriver_manager.chrome import ChromeDriverManager

from api.ipify.requests import IpifyAPI
from api.mts import MtsAPI
from db.engine import DatabaseEngine
from db.models import Accounts
from db.repository import cookies_repository, keys_repository
from handlers import register_user_commands
from loader import dp, bots_list
from settings import ALLOWED_SUBSCRIPTIONS
from utils.message_middleware import MessageMiddleware


async def generate_mts_cookies():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Запуск в безголовом режиме
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Использование WebDriver Manager для получения драйвера
    service = Service(ChromeDriverManager().install())
    print(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        await to_thread.run_sync(driver.get, "https://login.mts.ru/")
        await asyncio.sleep(5)  # Ожидание загрузки страницы

        cookies = driver.get_cookies()
        async with aiohttp.ClientSession() as session:
            ipify_api = IpifyAPI(session=session)
            response = await ipify_api.get_ip()

        cookies_data = await cookies_repository.get_cookies_info_by_ip_address(ip_address=response.ip_address)

        print(cookies)

        if not cookies_data:
            await cookies_repository.add_cookies(cookies=cookies, ip_address=response.ip_address)
        else:
            await cookies_repository.update_cookies_data(cookies_id=cookies_data.id, cookies=cookies)
    finally:
        driver.quit()  # Закрытие драйвера


async def restoration_of_subscriptions(account: Accounts):
    content_id = 0
    async with aiohttp.ClientSession() as session:
        mts_api = MtsAPI(session=session, ya_token=account.ya_token)
        try:
            response = await mts_api.get_tariff_now(phone_number=account.phone_number)
        except:
            return await restoration_of_subscriptions(account=account)
        if not bool(len(response.root)):
            await mts_api.activate_mts_premium(phone_number=account.phone_number,
                                               content_id=ALLOWED_SUBSCRIPTIONS[content_id])
        elif not response.root[0].isPremiumSubscriber:
            await mts_api.activate_mts_premium(phone_number=account.phone_number,
                                               content_id=ALLOWED_SUBSCRIPTIONS[content_id])


async def preparation_restoration_of_subscriptions():
    coupons = await keys_repository.get_all_coupons()
    filtered_coupons = [coupon for coupon in coupons if coupon.upd_date is not None]
    coupons = sorted(filtered_coupons, key=attrgetter('upd_date'), reverse=True)
    batch_size = 50
    phone_numbers = []
    for i in range(0, len(coupons), batch_size):
        batch = coupons[i:i + batch_size]
        accounts_tasks = []
        for coupon in batch:
            if not coupon.account:
                continue

            if coupon.account.phone_number.startswith('7') and coupon.account.phone_number not in phone_numbers:
                phone_numbers.append(coupon.account.phone_number)

            if coupon.subscription_id == 0 and coupon.account.phone_number.startswith('7'):
                accounts_tasks.append(asyncio.create_task(restoration_of_subscriptions(coupon.account)))

        await asyncio.gather(*accounts_tasks)


async def on_startup(dp):
    register_user_commands(dp)

    for bot in bots_list:
        print(await bot.get_me())
        await bot.delete_webhook(drop_pending_updates=True)

    await generate_mts_cookies()
    # await preparation_restoration_of_subscriptions()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(generate_mts_cookies, trigger=IntervalTrigger(minutes=15))
    # scheduler.add_job(preparation_restoration_of_subscriptions, trigger=IntervalTrigger(hours=1))
    scheduler.start()


async def main() -> None:
    # db_engine = DatabaseEngine()
    # await db_engine.proceed_schemas()
    await on_startup(dp)
    dp.message.middleware.register(MessageMiddleware())
    await dp.start_polling(*bots_list)


if __name__ == '__main__':
    asyncio.run(main())
