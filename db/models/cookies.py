from sqlalchemy import Column, Integer, JSON, String

from db.base import BaseModel, CleanModel


class Cookies(BaseModel, CleanModel):
    """Таблица аккаунтов"""
    __tablename__ = 'cookies'
    ip_address = Column(String, nullable=False)
    cookies = Column(JSON)

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
