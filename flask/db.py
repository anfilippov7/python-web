import atexit
from typing import Type, Union
import uuid
from cachetools import cached
from sqlalchemy import Column, String, Integer, DateTime, Text, create_engine, func, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy_utils import EmailType, UUIDType

PG_DSN = 'postgresql://postgres:1234@127.0.0.1:5431/add'
engine = create_engine(PG_DSN)
Base = declarative_base()
Session = sessionmaker(bind=engine)
atexit.register(engine.dispose)


class User(Base):
    __tablename__ = 'ad_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=True, unique=True, index=True)
    e_mail = Column(EmailType, nullable=True, unique=True)
    password = Column(String(150), nullable=True)
    registration_time = Column(DateTime, server_default=func.now())

    services = relationship('Service', backref='user')


class Token(Base):

    __tablename__ = "tokens"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    creation_time = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("ad_user.id", ondelete="CASCADE"))
    user = relationship("User", lazy="joined")


class Service(Base):
    __tablename__ = 'ad_service'

    id = Column(Integer, primary_key=True, autoincrement=True)
    heading = Column(String, nullable=True, unique=False, index=True)
    description = Column(Text, nullable=True)
    creation_time = Column(DateTime, server_default=func.now())

    user_id = Column(Integer, ForeignKey('ad_user.id'))

@cached({})
def get_engine():
    return create_engine(PG_DSN)


@cached({})
def get_session_maker():
    return sessionmaker(bind=get_engine())


ORM_MODEL_CLS = Union[Type[User], Type[Token]]
ORM_MODEL = Union[User, Token]

Base.metadata.create_all(bind=engine)
