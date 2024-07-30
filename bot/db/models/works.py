from sqlalchemy import Boolean, Column, Integer, String

from ..base import Base


class Works(Base):
    __tablename__ = "works"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    department_name = Column(String, nullable=True)
    delivery = Column(Integer, default=0, nullable=False)
    standard = Column(Integer, default=0, nullable=False)
