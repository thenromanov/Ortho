from sqlalchemy import orm, Integer, String, Column, Table, ForeignKey
from .dbSession import SqlAlchemyBase

association_table = Table('association', SqlAlchemyBase.metadata,
                          Column('user', Integer, ForeignKey('users.id'), nullable=True),
                          Column('mistake', Integer, ForeignKey('mistakes.id')))


class Mistake(SqlAlchemyBase):
    __tablename__ = 'mistakes'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    count = Column(Integer, nullable=True)
    language = Column(Integer, ForeignKey('languages.id'), nullable=True)
    users = orm.relation('User', secondary='association', back_populates='mistakes')

    def __repr__(self):
        return f'<Mistake> {self.id} {self.name}>'
