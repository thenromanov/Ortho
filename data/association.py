from sqlalchemy import orm, Integer, String, Column, Table, ForeignKey
from .dbSession import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Association(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'association'

    user = Column(Integer, ForeignKey('users.id'), primary_key=True)
    mistake = Column(Integer, ForeignKey('mistakes.id'), primary_key=True)
    count = Column(Integer, nullable=True)
    users = orm.relation('User', back_populates='mistakes')
    mistakes = orm.relation('Mistake', back_populates='users')
