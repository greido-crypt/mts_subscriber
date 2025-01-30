from sqlalchemy import Column, Integer, BigInteger, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped

from db.base import BaseModel, CleanModel
from .accounts import Accounts
from .users import Users


class Keys(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'keys'

    coupon = Column(String, nullable=False, unique=True)
    subscription_id = Column(BigInteger, nullable=False, default=0)

    account_id = Column(BigInteger, ForeignKey('accounts.id'), nullable=True)
    account: Mapped[Accounts] = relationship("Accounts", backref=__tablename__, cascade='all', lazy='subquery')

    user_id = Column(BigInteger, ForeignKey('users.user_id'), nullable=True)
    user: Mapped[Users] = relationship("Users", backref=__tablename__, cascade='all', lazy='subquery')

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
