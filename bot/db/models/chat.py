from sqlalchemy import Boolean, Column, String

from ..base import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    admin = Column(Boolean, default=False)
