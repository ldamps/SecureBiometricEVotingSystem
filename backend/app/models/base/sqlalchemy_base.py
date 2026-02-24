from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """ Root declarative base for all SQLAlchemy models. """
    metadata = MetaData(schema="public")