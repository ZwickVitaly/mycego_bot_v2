from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from ..base import Base


class Survey(Base):
    """
    Модель опроса
    РЕЗУЛЬТАТ survey_json НЕОБХОДИМО ПАРСИТЬ КАК JSON НА ВХОД И ВЫХОД
    """

    __tablename__ = "surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)  # id опроса
    user_id = Column(
        ForeignKey("user.id", ondelete="CASCADE")
    )  # id пользователя из бд
    period = Column(String, nullable=False)
    survey_json = Column(
        Text, nullable=False
    )  # результат опроса. хранится строкой, нужно парсить
    created_at = Column(
        DateTime, default=func.now(), nullable=False
    )  # дата прохождения опроса
    user = relationship(
        "User", back_populates="surveys", lazy="joined"
    )  # отношение к пользователю
