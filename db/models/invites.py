from typing import Sequence

from sqlalchemy import Column, String, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, relationship

from db.base import BaseModel, CleanModel
from .accounts import Accounts


class Invites(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'invites'

    invite_url = Column(String, nullable=False, unique=True)

    used_account_id = Column(BigInteger, ForeignKey('accounts.id'))

    used_account: Mapped[Accounts] = relationship("Accounts", backref='used_link_' + __tablename__, cascade='all', lazy='subquery',
                                                  foreign_keys=[used_account_id])

    account_id = Column(BigInteger, ForeignKey('accounts.id'))

    account: Mapped[Accounts] = relationship("Accounts", backref='created_link_' + __tablename__, cascade='all', lazy='subquery',
                                             foreign_keys=[account_id])

    @property
    def stats(self) -> str:
        """"
        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.id}>"

    def __repr__(self):
        return self.__str__()