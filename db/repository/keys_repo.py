from typing import List, Sequence

from sqlalchemy import select, update, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.engine import DatabaseEngine
from db.models import Keys


class KeysRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_code(self, coupon: str, subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                keys = Keys(
                    coupon=coupon,
                    subscription_id=subscription_id
                )
                try:
                    session.add(keys)
                except Exception:
                    return False
                return True

    async def add_codes(self, coupons: List[str], subscription_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                keys = []
                for coupon in coupons:
                    keys.append(Keys(coupon=coupon,
                                     subscription_id=subscription_id))
                try:
                    session.add_all(keys)
                except Exception:
                    return False
                return True

    async def get_coupon_info(self, coupon: str) -> Keys | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Keys).where(or_(Keys.coupon == coupon))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def get_coupons_by_user_id(self, user_id: int) -> list[Keys] | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Keys).where(or_(Keys.user_id == user_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def get_coupon_data_by_id(self, coupon_id: int) -> Keys | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Keys).where(or_(Keys.id == coupon_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def get_coupon_data_by_coupon(self, coupon: str) -> Keys | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Keys).where(or_(Keys.coupon == coupon))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def update_coupon_user_id(self, coupon_id: int, user_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Keys).values(
                    {
                        Keys.user_id: user_id
                    }
                ).where(or_(Keys.id == coupon_id))
                await session.execute(sql)
                await session.commit()

    async def update_coupon_account_id(self, coupon_id: int, account_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Keys).values(
                    {
                        Keys.account_id: account_id
                    }
                ).where(or_(Keys.id == coupon_id))
                await session.execute(sql)
                await session.commit()

    async def delete_coupon_account_id(self, coupon_id: int):
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = update(Keys).values(
                    {
                        Keys.account_id: None
                    }
                ).where(or_(Keys.id == coupon_id))
                await session.execute(sql)
                await session.commit()

    async def get_all_coupons(self) -> Sequence[Keys]:
        async with self.session_maker() as session:
            session: AsyncSession
            async with session.begin():
                sql = select(Keys)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()
