from typing import Union
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String


class DataModel(BaseModel):
    """
    Data model representing a user.

    Attributes:
        id (int): The unique identifier of the user.
        name (str): The name of the user.
    """

    id: int
    name: str


Base = declarative_base()


class Users(Base):
    """
    SQLAlchemy model for the Users table.

    Attributes:
        __tablename__ (str): The name of the table in the database.
        id (Column): The unique identifier of the user, primary key.
        name (Column): The name of the user.
    """

    __tablename__ = "Users"
    id = Column("id", Integer, primary_key=True, index=True)
    name = Column("name", String, index=True)


class ResponseModel(BaseModel):
    """
    Response model for API responses.

    Attributes:
        status (str): The status of the response (e.g., "Success" or "Failed").
        cached (bool): Indicates whether the response was retrieved from cache.
        response (dict): The actual response data, which can be a dictionary.
    """

    status: str
    cached: bool
    response: dict
