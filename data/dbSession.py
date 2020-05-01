import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as dec
from sqlalchemy.orm import Session

SqlAlchemyBase = dec.declarative_base()

__factory = None


def globalInit(dbFile):
    global __factory

    if __factory:
        return

    if not dbFile or not dbFile.strip():
        raise Exception('Необходимо указать файл базы данных')

    connStr = f'sqlite:///{dbFile.strip()}?check_same_thread=False'
    print(f'Подключение к базе данных по адресу {connStr}')

    engine = sa.create_engine(connStr, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    from . import __allModels

    SqlAlchemyBase.metadata.create_all(engine)


def createSession() -> Session:
    global __factory
    return __factory()
