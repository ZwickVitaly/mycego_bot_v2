from sqlalchemy import Boolean, Column, Integer, String

from ..base import Base


class Works(Base):
    __tablename__ = "works"

    id = Column(String, primary_key=True)
    name = Column(String)
    delivery = Column(Boolean, default=False)
    standard = Column(Integer, default=0)
