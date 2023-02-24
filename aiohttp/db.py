from cachetools import cached
from sqlalchemy import Column, Integer, String, func, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, relationship
from typing import Type, Union
import uuid
from sqlalchemy_utils import EmailType, UUIDType


PG_DSN = 'postgresql+asyncpg://app:1234@127.0.0.1:5430/aiohttp'
engine = create_async_engine(PG_DSN)
Session = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

class User(Base):
    __tablename__ = 'ad_user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True, nullable=False)
    e_mail = Column(EmailType, nullable=True, unique=True)
    password = Column(String, nullable=False)
    creation_time = Column(DateTime, server_default=func.now())

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
    return create_async_engine(PG_DSN)


@cached({})
def get_session_maker():
    return sessionmaker(bind=get_engine())



ORM_MODEL_CLS = Union[Type[User], Type[Token]]
ORM_MODEL = Union[User, Token]


