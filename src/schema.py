from typing import Union
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String


class DataModel(BaseModel):
    id: int
    name: str


Base = declarative_base()


class Users(Base):
    __tablename__ = "Users"
    id = Column("id", Integer, primary_key=True, index=True)
    name = Column("name", String, index=True)


class ResponseModel(BaseModel):
    status: str
    cached: bool
    response: Union[dict, list]
