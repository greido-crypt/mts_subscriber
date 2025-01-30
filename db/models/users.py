from sqlalchemy import Column, Integer, BigInteger, String

from db.base import BaseModel, CleanModel


class Users(BaseModel, CleanModel):
    """Таблица юзеров"""
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True, unique=True, nullable=False)
    username = Column(String, nullable=True, unique=False)

    @property
    def stats(self) -> str:
        """
        :return:
        """
        return ""

    def __str__(self) -> str:
        return f"<{self.__tablename__}:{self.user_id}>"

    def __repr__(self):
        return self.__str__()

    def keyboard_message(self):
        return (f'🔴 Добро пожаловать в ваш личный кабинет: 🔴\n'
                f'🔺 Telegram ID: {self.user_id}\n'
                f'🔺 Username: @{self.username}\n'
                f'🔺 Зарегистрирован: {self.creation_date}')
