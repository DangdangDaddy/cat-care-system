from pydantic import BaseModel
from datetime import date as dt_date, datetime as dt_datetime
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
    color: Optional[str] = None  # 毛色 (前端使用 color)
    birth_date: dt_date
    neutered: bool = False
    vaccination_status: Optional[str] = None
    deworming_date: Optional[dt_date] = None  # 驱虫日期
    medical_history: Optional[str] = None  # 病史记录
    internal_deworming_interval_days: Optional[int] = 90
    external_deworming_interval_days: Optional[int] = 180
    avatar: Optional[str] = None

class CatCreate(CatBase):
    pass

class CatUpdate(BaseModel):
    name: Optional[str] = None
    gender: Optional[str] = None
    breed: Optional[str] = None
    color: Optional[str] = None
    birth_date: Optional[dt_date] = None
    neutered: Optional[bool] = None
    vaccination_status: Optional[str] = None
    deworming_date: Optional[dt_date] = None
    medical_history: Optional[str] = None
    internal_deworming_interval_days: Optional[int] = None
    external_deworming_interval_days: Optional[int] = None
    avatar: Optional[str] = None

class Cat(CatBase):
    id: int
    owner_id: int
    class Config:
        from_attributes = True

class WeightRecordBase(BaseModel):
    date: dt_date
    weight: float
    note: Optional[str] = None

class WeightRecordCreate(WeightRecordBase):
    pass

class WeightRecordUpdate(BaseModel):
    date: Optional[dt_date] = None
    weight: Optional[float] = None
    note: Optional[str] = None

class WeightRecord(WeightRecordBase):
    id: int
    cat_id: int
    class Config:
        from_attributes = True

class PhotoTaggedCat(BaseModel):
    id: int
    name: str
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

# Medical History Schemas
class MedicalHistoryBase(BaseModel):
    record_type: str = "illness"
    sync_group_id: Optional[str] = None
    disease: str
    date: dt_date
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalHistoryCreate(MedicalHistoryBase):
    pass

class MedicalHistoryUpdate(BaseModel):
    record_type: Optional[str] = None
    sync_group_id: Optional[str] = None
    disease: Optional[str] = None
    date: Optional[dt_date] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None

class MedicalHistory(MedicalHistoryBase):
    id: int
    cat_id: int
    sync_group_size: Optional[int] = None
    created_at: dt_datetime
    class Config:
        from_attributes = True

# Photo Schemas
class PhotoBase(BaseModel):
    url: str
    thumbnail: Optional[str] = None
    description: Optional[str] = None
    album_id: Optional[int] = None
    captured_at: Optional[dt_datetime] = None
    sort_order: Optional[float] = None
    is_pinned: bool = False

class PhotoCreate(PhotoBase):
    pass

class PhotoUpdate(BaseModel):
    description: Optional[str] = None
    album_id: Optional[int] = None
    tag_cat_ids: Optional[List[int]] = None
    is_pinned: Optional[bool] = None

class PhotoTagRecommendation(BaseModel):
    cat_id: int
    cat_name: str
    confidence: float

class PhotoTagRecommendationResponse(BaseModel):
    recommendations: List[PhotoTagRecommendation]

class PhotoReorderRequest(BaseModel):
    user_id: int
    photo_id: int
    prev_photo_id: Optional[int] = None
    next_photo_id: Optional[int] = None

class Photo(PhotoBase):
    id: int
    cat_id: int
    created_at: dt_datetime
    cats: List[PhotoTaggedCat] = []
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
    created_at: dt_datetime
    class Config:
        from_attributes = True

class AlbumWithPhotos(Album):
    photos: List[Photo] = []


class FeedingPlanBase(BaseModel):
    name: str
    start_date: dt_date
    end_date: Optional[dt_date] = None
    food_type: str
    brand: Optional[str] = None
    product_name: str
    life_stage: Optional[str] = None
    complete_balance_status: str = "pending"
    daily_amount: Optional[float] = None
    amount_unit: Optional[str] = None
    feeding_frequency: Optional[str] = None
    daily_calories: Optional[float] = None
    hydration_strategy: Optional[str] = None
    notes: Optional[str] = None
    sync_group_id: Optional[str] = None
    is_active: bool = True


class FeedingPlanCreate(FeedingPlanBase):
    pass


class FeedingPlanUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[dt_date] = None
    end_date: Optional[dt_date] = None
    food_type: Optional[str] = None
    brand: Optional[str] = None
    product_name: Optional[str] = None
    life_stage: Optional[str] = None
    complete_balance_status: Optional[str] = None
    daily_amount: Optional[float] = None
    amount_unit: Optional[str] = None
    feeding_frequency: Optional[str] = None
    daily_calories: Optional[float] = None
    hydration_strategy: Optional[str] = None
    notes: Optional[str] = None
    sync_group_id: Optional[str] = None
    is_active: Optional[bool] = None


class FeedingPlan(FeedingPlanBase):
    id: int
    cat_id: int
    sync_group_size: Optional[int] = None
    created_at: dt_datetime
    updated_at: dt_datetime

    class Config:
        from_attributes = True


class FoodTransitionStepBase(BaseModel):
    day_index: int
    old_food_ratio: int
    new_food_ratio: int
    notes: Optional[str] = None


class FoodTransitionStepCreate(FoodTransitionStepBase):
    pass


class FoodTransitionStep(FoodTransitionStepBase):
    id: int
    transition_plan_id: int
    created_at: dt_datetime

    class Config:
        from_attributes = True


class FoodTransitionPlanBase(BaseModel):
    name: str
    start_date: dt_date
    planned_days: int = 7
    old_food_name: str
    new_food_name: str
    reason: Optional[str] = None
    status: str = "planned"
    end_date: Optional[dt_date] = None
    stop_reason: Optional[str] = None
    observation_notes: Optional[str] = None
    sync_group_id: Optional[str] = None


class FoodTransitionPlanCreate(FoodTransitionPlanBase):
    steps: List[FoodTransitionStepCreate] = []


class FoodTransitionPlanUpdate(BaseModel):
    name: Optional[str] = None
    start_date: Optional[dt_date] = None
    planned_days: Optional[int] = None
    old_food_name: Optional[str] = None
    new_food_name: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = None
    end_date: Optional[dt_date] = None
    stop_reason: Optional[str] = None
    observation_notes: Optional[str] = None
    sync_group_id: Optional[str] = None
    steps: Optional[List[FoodTransitionStepCreate]] = None


class FoodTransitionPlan(FoodTransitionPlanBase):
    id: int
    cat_id: int
    sync_group_size: Optional[int] = None
    created_at: dt_datetime
    updated_at: dt_datetime
    steps: List[FoodTransitionStep] = []

    class Config:
        from_attributes = True


class SupplementCourseBase(BaseModel):
    product_name: str
    category: Optional[str] = None
    purpose: Optional[str] = None
    start_date: dt_date
    end_date: Optional[dt_date] = None
    frequency: Optional[str] = None
    dosage: Optional[float] = None
    dosage_unit: Optional[str] = None
    feeding_method: Optional[str] = None
    source: Optional[str] = None
    response: Optional[str] = None
    risk_notes: Optional[str] = None
    sync_group_id: Optional[str] = None
    is_active: bool = True


class SupplementCourseCreate(SupplementCourseBase):
    pass


class SupplementCourseUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    purpose: Optional[str] = None
    start_date: Optional[dt_date] = None
    end_date: Optional[dt_date] = None
    frequency: Optional[str] = None
    dosage: Optional[float] = None
    dosage_unit: Optional[str] = None
    feeding_method: Optional[str] = None
    source: Optional[str] = None
    response: Optional[str] = None
    risk_notes: Optional[str] = None
    sync_group_id: Optional[str] = None
    is_active: Optional[bool] = None


class SupplementCourse(SupplementCourseBase):
    id: int
    cat_id: int
    sync_group_size: Optional[int] = None
    created_at: dt_datetime
    updated_at: dt_datetime

    class Config:
        from_attributes = True


class FeedingRecordBase(BaseModel):
    recorded_at: dt_datetime
    record_type: str
    brand: Optional[str] = None
    item_name: str
    flavor: Optional[str] = None
    amount: Optional[float] = None
    amount_unit: Optional[str] = None
    calories: Optional[float] = None
    consumed_status: Optional[str] = "finished"
    feeding_method: Optional[str] = None
    notes: Optional[str] = None
    reaction: Optional[str] = "none"
    sync_group_id: Optional[str] = None
    plan_id: Optional[int] = None
    transition_plan_id: Optional[int] = None


class FeedingRecordCreate(FeedingRecordBase):
    pass


class FeedingRecordUpdate(BaseModel):
    recorded_at: Optional[dt_datetime] = None
    record_type: Optional[str] = None
    brand: Optional[str] = None
    item_name: Optional[str] = None
    flavor: Optional[str] = None
    amount: Optional[float] = None
    amount_unit: Optional[str] = None
    calories: Optional[float] = None
    consumed_status: Optional[str] = None
    feeding_method: Optional[str] = None
    notes: Optional[str] = None
    reaction: Optional[str] = None
    sync_group_id: Optional[str] = None
    plan_id: Optional[int] = None
    transition_plan_id: Optional[int] = None


class FeedingRecord(FeedingRecordBase):
    id: int
    cat_id: int
    sync_group_size: Optional[int] = None
    created_at: dt_datetime
    updated_at: dt_datetime

    class Config:
        from_attributes = True


class FeedingOverview(BaseModel):
    active_plan: Optional[FeedingPlan] = None
    active_transition_plan: Optional[FoodTransitionPlan] = None
    active_supplement_courses: List[SupplementCourse] = []
    today_records: List[FeedingRecord] = []
    recent_reactions: List[FeedingRecord] = []
    daily_summary: dict


class FeedingPlanBatchCreateRequest(BaseModel):
    cat_ids: List[int]
    plan: FeedingPlanCreate


class FeedingRecordBatchCreateRequest(BaseModel):
    cat_ids: List[int]
    record: FeedingRecordCreate


class FoodTransitionPlanBatchCreateRequest(BaseModel):
    cat_ids: List[int]
    transition: FoodTransitionPlanCreate


class SupplementCourseBatchCreateRequest(BaseModel):
    cat_ids: List[int]
    course: SupplementCourseCreate
