from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    cats = relationship("Cat", back_populates="owner")

class Cat(Base):
    __tablename__ = "cats"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    gender = Column(String)  # male/female
    breed = Column(String)  # 品种
    coat_color = Column(String, nullable=True)  # 毛色
    birth_date = Column(Date)
    neutered = Column(Boolean, default=False)
    vaccination_status = Column(String, nullable=True)  # 疫苗接种状态
    last_internal_deworming = Column(Date, nullable=True)  # 最近体内驱虫
    last_external_deworming = Column(Date, nullable=True)  # 最近体外驱虫
    avatar = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="cats")
    weights = relationship("WeightRecord", back_populates="cat", cascade="all, delete-orphan")
    medical_histories = relationship("MedicalHistory", back_populates="cat", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="cat", cascade="all, delete-orphan")
    albums = relationship("Album", back_populates="cat", cascade="all, delete-orphan")

class WeightRecord(Base):
    __tablename__ = "weight_records"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    date = Column(Date)
    weight = Column(Float)  # 单位：克
    cat = relationship("Cat", back_populates="weights")

class MedicalHistory(Base):
    __tablename__ = "medical_histories"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    disease = Column(String, nullable=False)  # 疾病名称
    date = Column(Date, nullable=False)  # 发病日期
    treatment = Column(Text, nullable=True)  # 治疗方案
    notes = Column(Text, nullable=True)  # 备注
    created_at = Column(DateTime, default=datetime.utcnow)
    cat = relationship("Cat", back_populates="medical_histories")

class Album(Base):
    __tablename__ = "albums"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    name = Column(String, nullable=False)  # 相册名称
    cover_photo_id = Column(Integer, ForeignKey("photos.id"), nullable=True)  # 封面照片
    created_at = Column(DateTime, default=datetime.utcnow)
    cat = relationship("Cat", back_populates="albums")
    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan", foreign_keys="Photo.album_id")
    cover_photo = relationship("Photo", foreign_keys=[cover_photo_id], post_update=True)

class Photo(Base):
    __tablename__ = "photos"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    album_id = Column(Integer, ForeignKey("albums.id"), nullable=True)
    url = Column(String, nullable=False)  # 照片URL
    thumbnail = Column(String, nullable=True)  # 缩略图URL
    description = Column(Text, nullable=True)  # 描述
    created_at = Column(DateTime, default=datetime.utcnow)
    cat = relationship("Cat", back_populates="photos")
    album = relationship("Album", back_populates="photos", foreign_keys=[album_id])
