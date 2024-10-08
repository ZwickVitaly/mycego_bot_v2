from sqlalchemy import Column, Integer, String

from ..base import Base


class Works(Base):
    """
    Модель нормативов
    """

    __tablename__ = "works"

    id = Column(Integer, primary_key=True, autoincrement=True)  # внутренний id
    site_id = Column(String)  # id работы с сайта
    name = Column(String, nullable=False)  # название с сайта
    department_name = Column(String, nullable=True)  # название департамента с сайта
    delivery = Column(Integer, default=0, nullable=False)  # доставка с сайта
    standard = Column(Integer, default=0, nullable=False)  # стандарт с сайта
