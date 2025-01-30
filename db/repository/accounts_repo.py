from sqlalchemy import select, or_, update, all_, and_

from db.engine import DatabaseEngine
from db.models import Accounts


class AccountsRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_account(self, phone_number: str,
                          cookies: list[dict],
                          ya_token: str,
                          user_id: int = None):
        async with self.session_maker() as session:
            async with session.begin():
                phones = Accounts(phone_number=phone_number,
                                  cookies=cookies,
                                  ya_token=ya_token,
                                  user_id=user_id
                                  )
                try:
                    session.add(phones)
                except Exception:
                    return False
                return True

    async def get_account_info(self, phone_number: str) -> Accounts | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(or_(Accounts.phone_number == phone_number))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def get_account_by_id(self, account_id: int) -> Accounts | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(or_(Accounts.id == account_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def update_account_data(self, account_id: int):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_deleted: True
                    }
                ).where(or_(Accounts.id == account_id))
                await session.execute(sql)
                await session.commit()

    async def update_account_full_data(self, account_id: int, cookies: list[dict], ya_token: str):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values(
                    {
                        Accounts.is_deleted: False,
                        Accounts.cookies: cookies,
                        Accounts.ya_token: ya_token,
                    }
                ).where(or_(Accounts.id == account_id))
                await session.execute(sql)
                await session.commit()

    async def get_accounts_by_user_id(self, user_id: int, is_deleted: bool = False) -> list[Accounts] | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts).where(and_(Accounts.user_id == user_id, Accounts.is_deleted == is_deleted))
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def get_all_accounts(self) -> list[Accounts]:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Accounts)
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def update_account_data_by_account_id(self, user_id: int, account_id: int):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Accounts).values({
                    Accounts.user_id: user_id
                }
                ).where(Accounts.id == account_id)
                await session.execute(sql)
                await session.commit()
