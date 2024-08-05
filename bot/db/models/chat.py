from sqlalchemy import Boolean, Column, String

from ..base import Base


class Chat(Base):
    """
    Модель чата
    """

    __tablename__ = "chats"

    id = Column(String, primary_key=True)  # telegram chat id
    admin = Column(Boolean, default=False)  # есть ли админ права у бота в этом чате
