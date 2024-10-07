from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from ..base import Base


class User(Base):
    """
    Модель пользователя
    """

    __tablename__ = "user"

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # id пользователя в бд бота (остался из-за peewee)
    telegram_id = Column(
        String, unique=True, nullable=False
    )  # telegram id пользователя
    site_user_id = Column(String, unique=True, nullable=True)  # id на сайте
    username = Column(String, unique=True, nullable=True)  # username на сайте
    username_tg = Column(String, nullable=True)  # username пользователя в telegram
    first_name = Column(String, nullable=True)  # из telegram
    last_name = Column(String, nullable=True)  # из telegram
    role = Column(String, nullable=True)  # должность с сайта
    messages = relationship(
        "Message", back_populates="user", lazy="selectin"
    )  # отношение к сообщениям
    surveys = relationship(
        "Survey", back_populates="user", lazy="selectin"
    )  # отношение к опросам
