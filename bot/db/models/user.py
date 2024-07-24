from sqlalchemy import Column, String
from sqlalchemy.orm import relationship

from ..base import Base


class User(Base):
    __tablename__ = "users"

    telegram_id = Column(String, primary_key=True)
    site_user_id = Column(String, unique=True, nullable=True)
    username = Column(String, unique=True, nullable=True)
    username_tg = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    role = Column(String, nullable=True)
    messages = relationship("Message", back_populates="user", lazy="selectin")
