from sqlalchemy import Column, String, JSON, BigInteger, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, relationship

from db.base import BaseModel, CleanModel
from .users import Users


class Accounts(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'accounts'

    phone_number = Column(String, nullable=False, unique=False)
    ya_token = Column(String, nullable=False, unique=False)
    cookies = Column(JSON)
    is_deleted = Column(Boolean, nullable=False, default=False)
    user_id = Column(BigInteger, ForeignKey('users.user_id'))

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
