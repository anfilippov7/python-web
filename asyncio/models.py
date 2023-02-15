from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


PG_DSN = 'postgresql+asyncpg://user:1234@127.0.0.1:5431/starwars'

engine = create_async_engine(PG_DSN)
Session = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class SwapiPeople(Base):

    __tablename__ = 'swapi_people'

    id = Column(Integer, primary_key=True, autoincrement=True)
    birth_year = Column(String(200), nullable=True)
    eye_color = Column(String(150), nullable=True)
    films = Column(Text, nullable=True)
    gender = Column(String(50), nullable=True)
    hair_color = Column(String(50), nullable=True)
    height = Column(String(50), nullable=True)
    homeworld = Column(Text, nullable=True)
    mass = Column(String(50), nullable=True)
    name = Column(String(50), nullable=True)
    skin_color = Column(String(50), nullable=True)
    species = Column(Text, nullable=True)
    starships = Column(Text, nullable=True)
    vehicles = Column(Text, nullable=True)