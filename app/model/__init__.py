import logging

import inflect
from environs import Env
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declared_attr, declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


env = Env()
env.read_env()

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test")

engine = create_engine(env("DB_URL"), connect_args={"check_same_thread": False})

DBSession = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


class CustomBase:
    @declared_attr
    def __tablename__(cls):
        return inflect.engine().plural(cls.__name__.lower())


Base = declarative_base(cls=CustomBase)
