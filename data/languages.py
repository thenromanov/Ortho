from sqlalchemy import Integer, String, Column
from .dbSession import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Language(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'languages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    acronym = Column(String, nullable=True, unique=True)

    def __repr__(self):
        return f'<Language> {self.id} {self.acronym}'
