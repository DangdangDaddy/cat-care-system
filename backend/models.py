from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, Text, DateTime, UniqueConstraint
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
    color = Column(String, nullable=True)  # 毛色
    birth_date = Column(Date)
    neutered = Column(Boolean, default=False)
    vaccination_status = Column(String, nullable=True)  # 疫苗接种状态
    deworming_date = Column(Date, nullable=True)  # 驱虫日期
    medical_history = Column(Text, nullable=True)  # 病史记录
    internal_deworming_interval_days = Column(Integer, nullable=False, default=90)  # 体内驱虫频率
    external_deworming_interval_days = Column(Integer, nullable=False, default=180)  # 体外驱虫频率
    avatar = Column(String, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="cats")
    weights = relationship("WeightRecord", back_populates="cat", cascade="all, delete-orphan")
    medical_histories = relationship("MedicalHistory", back_populates="cat", cascade="all, delete-orphan")
    photos = relationship("Photo", back_populates="cat", cascade="all, delete-orphan")
    albums = relationship("Album", back_populates="cat", cascade="all, delete-orphan")
    photo_tags = relationship("PhotoCatTag", back_populates="cat", cascade="all, delete-orphan")
    feeding_plans = relationship("FeedingPlan", back_populates="cat", cascade="all, delete-orphan")
    feeding_records = relationship("FeedingRecord", back_populates="cat", cascade="all, delete-orphan")
    food_transition_plans = relationship("FoodTransitionPlan", back_populates="cat", cascade="all, delete-orphan")
    supplement_courses = relationship("SupplementCourse", back_populates="cat", cascade="all, delete-orphan")

class WeightRecord(Base):
    __tablename__ = "weight_records"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    date = Column(Date)
    weight = Column(Float)  # 单位：克
    note = Column(Text, nullable=True)  # 备注
    cat = relationship("Cat", back_populates="weights")

class MedicalHistory(Base):
    __tablename__ = "medical_histories"
    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"))
    record_type = Column(String, nullable=True, default="illness")  # 记录类型
    sync_group_id = Column(String, nullable=True, index=True)  # 同步组ID
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
    file_hash = Column(String, nullable=True, index=True)
    captured_at = Column(DateTime, nullable=True)
    sort_order = Column(Float, nullable=False, default=0)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    cat = relationship("Cat", back_populates="photos")
    album = relationship("Album", back_populates="photos", foreign_keys=[album_id])
    tagged_cats = relationship("PhotoCatTag", back_populates="photo", cascade="all, delete-orphan")

class PhotoCatTag(Base):
    __tablename__ = "photo_cat_tags"
    __table_args__ = (
        UniqueConstraint("photo_id", "cat_id", name="uq_photo_cat_tag"),
    )

    id = Column(Integer, primary_key=True, index=True)
    photo_id = Column(Integer, ForeignKey("photos.id"), nullable=False)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    photo = relationship("Photo", back_populates="tagged_cats")
    cat = relationship("Cat", back_populates="photo_tags")


class FeedingPlan(Base):
    __tablename__ = "feeding_plans"

    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    food_type = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    product_name = Column(String, nullable=False)
    life_stage = Column(String, nullable=True)
    complete_balance_status = Column(String, nullable=False, default="pending")
    daily_amount = Column(Float, nullable=True)
    amount_unit = Column(String, nullable=True)
    feeding_frequency = Column(String, nullable=True)
    daily_calories = Column(Float, nullable=True)
    hydration_strategy = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    sync_group_id = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cat = relationship("Cat", back_populates="feeding_plans")
    feeding_records = relationship("FeedingRecord", back_populates="plan")


class FoodTransitionPlan(Base):
    __tablename__ = "food_transition_plans"

    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    name = Column(String, nullable=False)
    start_date = Column(Date, nullable=False)
    planned_days = Column(Integer, nullable=False, default=7)
    old_food_name = Column(String, nullable=False)
    new_food_name = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    status = Column(String, nullable=False, default="planned")
    end_date = Column(Date, nullable=True)
    stop_reason = Column(Text, nullable=True)
    observation_notes = Column(Text, nullable=True)
    sync_group_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cat = relationship("Cat", back_populates="food_transition_plans")
    steps = relationship(
        "FoodTransitionStep",
        back_populates="transition_plan",
        cascade="all, delete-orphan",
        order_by="FoodTransitionStep.day_index.asc()",
    )
    feeding_records = relationship("FeedingRecord", back_populates="transition_plan")


class FoodTransitionStep(Base):
    __tablename__ = "food_transition_steps"

    id = Column(Integer, primary_key=True, index=True)
    transition_plan_id = Column(Integer, ForeignKey("food_transition_plans.id"), nullable=False, index=True)
    day_index = Column(Integer, nullable=False)
    old_food_ratio = Column(Integer, nullable=False)
    new_food_ratio = Column(Integer, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    transition_plan = relationship("FoodTransitionPlan", back_populates="steps")


class SupplementCourse(Base):
    __tablename__ = "supplement_courses"

    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=True)
    purpose = Column(String, nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    frequency = Column(String, nullable=True)
    dosage = Column(Float, nullable=True)
    dosage_unit = Column(String, nullable=True)
    feeding_method = Column(String, nullable=True)
    source = Column(String, nullable=True)
    response = Column(String, nullable=True)
    risk_notes = Column(Text, nullable=True)
    sync_group_id = Column(String, nullable=True, index=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cat = relationship("Cat", back_populates="supplement_courses")


class FeedingRecord(Base):
    __tablename__ = "feeding_records"

    id = Column(Integer, primary_key=True, index=True)
    cat_id = Column(Integer, ForeignKey("cats.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("feeding_plans.id"), nullable=True)
    transition_plan_id = Column(Integer, ForeignKey("food_transition_plans.id"), nullable=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    record_type = Column(String, nullable=False)
    brand = Column(String, nullable=True)
    item_name = Column(String, nullable=False)
    flavor = Column(String, nullable=True)
    amount = Column(Float, nullable=True)
    amount_unit = Column(String, nullable=True)
    calories = Column(Float, nullable=True)
    consumed_status = Column(String, nullable=True, default="finished")
    feeding_method = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    reaction = Column(String, nullable=True, default="none")
    sync_group_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    cat = relationship("Cat", back_populates="feeding_records")
    plan = relationship("FeedingPlan", back_populates="feeding_records")
    transition_plan = relationship("FoodTransitionPlan", back_populates="feeding_records")
