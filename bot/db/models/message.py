from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from ..base import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(
        ForeignKey("user.id", ondelete="DO NOTHING"),
        nullable=False,
    )
    text = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.now(), nullable=False)
    user = relationship("User", back_populates="messages", lazy="joined")

    def __str__(self):
        return self.text
