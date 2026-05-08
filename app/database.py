from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import DATABASE_URL

# this helps us connect python and postgres
engine = create_engine(DATABASE_URL)

# a sesh is like a convo with the db
# in a given session, we can do read and writes then clsoe it
# we create them as needded
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass