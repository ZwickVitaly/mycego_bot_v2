from sqlalchemy import Column, String, Boolean

from ..base import Base


class Chat(Base):
    __tablename__ = "chats"

    id = Column(String, primary_key=True)
    admin = Column(Boolean, default=False)
