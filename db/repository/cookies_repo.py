from sqlalchemy import select, update, or_

from db.engine import DatabaseEngine
from db.models import Cookies


class CookiesRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_cookies(self, cookies: list[dict], ip_address: str):
        async with self.session_maker() as session:
            async with session.begin():
                cookies = Cookies(
                    cookies=cookies,
                    ip_address=ip_address
                )
                try:
                    session.add(cookies)
                except Exception:
                    return False
                return True

    async def get_cookies_info_by_id(self, cookies_id: int) -> Cookies | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cookies).where(or_(Cookies.id == cookies_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def get_cookies_info_by_ip_address(self, ip_address: str) -> Cookies | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Cookies).where(or_(Cookies.ip_address == ip_address))
                sql_res = await session.execute(sql)
                return sql_res.scalar_one_or_none()

    async def update_cookies_data(self, cookies_id: int, cookies: list[dict]):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Cookies).values(
                    {
                        Cookies.cookies: cookies
                    }
                ).where(or_(Cookies.id == cookies_id))
                await session.execute(sql)
                await session.commit()