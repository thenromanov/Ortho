from sqlalchemy import orm, Integer, String, Column, Table, ForeignKey
from .dbSession import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Mistake(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'mistakes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    count = Column(Integer, nullable=True)
    language = Column(Integer, ForeignKey('languages.id'), nullable=True)
    users = orm.relation('Association', back_populates='mistakes')

    def __repr__(self):
        return f'<Mistake> {self.id} {self.name}>'
