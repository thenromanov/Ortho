from sqlalchemy import Integer, String, Column
from .dbSession import SqlAlchemyBase


class Language(SqlAlchemyBase):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    acronym = Column(String, nullable=True, unique=True)
