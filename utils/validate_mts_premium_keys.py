import asyncio

from db.repository import keys_repository

with open('../check_keys.txt', 'r') as f:
    keys = f.read().splitlines()


async def main():
    for key in keys:
        key_data = await keys_repository.get_coupon_data_by_coupon(key)
        if key_data.account_id:
            continue
        else:
            print(key)


asyncio.run(main())