from sqlalchemy import Boolean, Column, Integer, String

from ..base import Base


class Works(Base):
    """
    Модель нормативов
    """

    __tablename__ = "works"

    id = Column(String, primary_key=True)  # id работы с сайта
    name = Column(String, nullable=False)  # название с сайта
    department_name = Column(String, nullable=True)  # название департамента с сайта
    delivery = Column(Integer, default=0, nullable=False)  # доставка с сайта
    standard = Column(Integer, default=0, nullable=False)  # стандарт с сайта
