from pydantic import BaseModel
from datetime import date, datetime
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
    coat_color: Optional[str] = None
    birth_date: date
    neutered: bool = False
    vaccination_status: Optional[str] = None
    last_internal_deworming: Optional[date] = None
    last_external_deworming: Optional[date] = None
    avatar: Optional[str] = None

class CatCreate(CatBase):
    pass

class CatUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    breed: Optional[str] = None
    coat_color: Optional[str] = None
    birth_date: Optional[date] = None
    neutered: Optional[bool] = None
    vaccination_status: Optional[str] = None
    last_internal_deworming: Optional[date] = None
    last_external_deworming: Optional[date] = None
    avatar: Optional[str] = None

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

class WeightRecordUpdate(BaseModel):
    date: Optional[date] = None
    weight: Optional[float] = None

class WeightRecord(WeightRecordBase):
    id: int
    cat_id: int
    class Config:
        from_attributes = True

# Medical History Schemas
class MedicalHistoryBase(BaseModel):
    disease: str
    date: date
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryUpdate(BaseModel):
    disease: Optional[str] = None
    date: Optional[date] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalHistory(MedicalHistoryBase):
    id: int
    cat_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Photo Schemas
class PhotoBase(BaseModel):
    url: str
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    album_id: Optional[int] = None

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(BaseModel):
    description: Optional[str] = None
    album_id: Optional[int] = None

class Photo(PhotoBase):
    id: int
    cat_id: int
    created_at: datetime
    class Config:
        from_attributes = True

# Album Schemas
class AlbumBase(BaseModel):
    name: str
    cover_photo_id: Optional[int] = None

class AlbumCreate(AlbumBase):
    pass

class AlbumUpdate(BaseModel):
    name: Optional[str] = None
    cover_photo_id: Optional[int] = None

class Album(AlbumBase):
    id: int
    cat_id: int
    created_at: datetime
    class Config:
        from_attributes = True

class AlbumWithPhotos(Album):
    photos: List[Photo] = []
