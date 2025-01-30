from sqlalchemy import select, update, or_, Sequence

from db.engine import DatabaseEngine
from db.models import Invites


class InvitesRepository:
    def __init__(self):
        self.session_maker = DatabaseEngine().create_session()

    async def add_invite(self, invite_url: str, account_id: int = None):
        async with self.session_maker() as session:
            async with session.begin():
                invites = Invites(invite_url=invite_url, account_id=account_id
                                  )
                try:
                    session.add(invites)
                except Exception:
                    return False
                return True

    async def get_invite_info_by_id(self, invite_id: int) -> Invites | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Invites).where(or_(Invites.id == invite_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def get_invites_by_account_id(self, account_id: int) -> Sequence[Invites] | None:
        async with self.session_maker() as session:
            async with session.begin():
                sql = select(Invites).where(or_(Invites.account_id == account_id))
                sql_res = await session.execute(sql)
                return sql_res.scalars().all()

    async def get_invites(self, is_used=False) -> Sequence[Invites] | None:
        async with self.session_maker() as session:
            async with session.begin():
                if is_used:
                    sql = select(Invites).where(Invites.used_account_id != None)
                else:
                    sql = select(Invites).where(Invites.used_account_id == None)
                sql_res = await session.execute(sql)
                return sql_res.scalars().one_or_none()

    async def update_invite_used_account_id(self, invite_id: int, used_account_id: int):
        async with self.session_maker() as session:
            async with session.begin():
                sql = update(Invites).values(
                    {
                        Invites.used_account_id: used_account_id
                    }
                ).where(or_(Invites.id == invite_id))
                await session.execute(sql)
                await session.commit()
