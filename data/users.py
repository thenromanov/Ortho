from sqlalchemy import orm, Integer, String, Column
from .dbSession import SqlAlchemyBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    surname = Column(String, nullable=True)
    name = Column(String, nullable=True)
    age = Column(Integer, nullable=True)
    email = Column(String, index=True, unique=True, nullable=True)
    hashedPassword = Column(String, nullable=True)
    mistakes = orm.relation('Mistake', secondary='association', back_populates='users')

    def __repr__(self):
        return f'<User> {self.id} {self.surname} {self.name}'

    def setPassword(self, password):
        self.hashedPassword = generate_password_hash(password)

    def checkPassword(self, password):
        return check_password_hash(self.hashedPassword, password)
