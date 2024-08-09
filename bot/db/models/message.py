from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..base import Base


class Message(Base):
    """
    Модель сообщения В ГЛАВНОЕ МЕНЮ
    """

    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)  # id сообщения
    user_id = Column(
        ForeignKey("user.id", ondelete="NO ACTION"),  # связка с пользователем
        nullable=False,
    )
    text = Column(String, nullable=False)  # текст сообщения
    timestamp = Column(
        DateTime, default=datetime.now(), nullable=False
    )  # время сообщения
    user = relationship(
        "User", back_populates="messages", lazy="joined"
    )  # отношение к пользователю

    def __str__(self):
        return self.text
