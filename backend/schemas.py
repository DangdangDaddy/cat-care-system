from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    class Config:
        from_attributes = True

class CatBase(BaseModel):
    name: str
    gender: str
    breed: str
    birth_date: date
    neutered: bool = False
    avatar: Optional[str] = None

class CatCreate(CatBase):
    pass

class Cat(CatBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class WeightRecordBase(BaseModel):
    date: date
    weight: float

class WeightRecordCreate(WeightRecordBase):
    pass

class WeightRecord(WeightRecordBase):
    id: int
    cat_id: int
    class Config:
        from_attributes = True
