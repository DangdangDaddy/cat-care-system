import sqlite3
import uuid
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import joinedload
from pathlib import Path
from database import engine, SessionLocal
import models
from routers import auth, cats, weights, medical_history, photos, albums, feeding
from photo_utils import compute_file_hash, extract_captured_at, save_thumbnail

models.Base.metadata.create_all(bind=engine)


def ensure_health_record_schema() -> None:
    """为现有 SQLite 数据库补齐健康记录的兼容字段。"""
    db_path = Path(__file__).parent / "cat_care.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(medical_histories)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "record_type" not in existing_columns:
            cursor.execute(
                "ALTER TABLE medical_histories ADD COLUMN record_type VARCHAR DEFAULT 'illness'"
            )
        if "sync_group_id" not in existing_columns:
            cursor.execute("ALTER TABLE medical_histories ADD COLUMN sync_group_id VARCHAR")
        conn.commit()
    finally:
        conn.close()


ensure_health_record_schema()


def ensure_cat_health_settings_schema() -> None:
    """补齐猫咪健康设置字段（驱虫频率等）。"""
    db_path = Path(__file__).parent / "cat_care.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(cats)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "internal_deworming_interval_days" not in existing_columns:
            cursor.execute(
                "ALTER TABLE cats ADD COLUMN internal_deworming_interval_days INTEGER NOT NULL DEFAULT 90"
            )
        if "external_deworming_interval_days" not in existing_columns:
            cursor.execute(
                "ALTER TABLE cats ADD COLUMN external_deworming_interval_days INTEGER NOT NULL DEFAULT 180"
            )

        cursor.execute(
            "UPDATE cats SET internal_deworming_interval_days = 90 WHERE internal_deworming_interval_days IS NULL"
        )
        cursor.execute(
            "UPDATE cats SET external_deworming_interval_days = 180 WHERE external_deworming_interval_days IS NULL"
        )
        conn.commit()
    finally:
        conn.close()


ensure_cat_health_settings_schema()


def backfill_health_record_sync_groups() -> None:
    """把跨猫咪的相同健康记录补成同一同步组，便于后续联动编辑。"""
    db = SessionLocal()
    try:
        records = (
            db.query(models.MedicalHistory)
            .order_by(
                models.MedicalHistory.record_type.asc(),
                models.MedicalHistory.disease.asc(),
                models.MedicalHistory.date.asc(),
                models.MedicalHistory.id.asc(),
            )
            .all()
        )

        buckets: dict[tuple, list[models.MedicalHistory]] = {}
        for record in records:
            key = (
                record.record_type or "illness",
                record.disease,
                record.date,
                record.treatment or "",
                record.notes or "",
            )
            buckets.setdefault(key, []).append(record)

        changed = False
        for bucket in buckets.values():
            unique_cat_ids = {record.cat_id for record in bucket}
            if len(unique_cat_ids) < 2:
                continue

            existing_group_id = next((record.sync_group_id for record in bucket if record.sync_group_id), None)
            group_id = existing_group_id or str(uuid.uuid4())
            for record in bucket:
                if record.sync_group_id != group_id:
                    record.sync_group_id = group_id
                    changed = True

        if changed:
            db.commit()
    finally:
        db.close()


backfill_health_record_sync_groups()


def ensure_photo_schema() -> None:
    """为现有 SQLite 数据库补齐照片排序/去重相关字段。"""
    db_path = Path(__file__).parent / "cat_care.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(photos)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        if "file_hash" not in existing_columns:
            cursor.execute("ALTER TABLE photos ADD COLUMN file_hash VARCHAR")
        if "captured_at" not in existing_columns:
            cursor.execute("ALTER TABLE photos ADD COLUMN captured_at DATETIME")
        if "sort_order" not in existing_columns:
            cursor.execute("ALTER TABLE photos ADD COLUMN sort_order REAL DEFAULT 0")
        if "is_pinned" not in existing_columns:
            cursor.execute("ALTER TABLE photos ADD COLUMN is_pinned BOOLEAN DEFAULT 0")
        conn.commit()
    finally:
        conn.close()


ensure_photo_schema()


def ensure_feeding_schema() -> None:
    """补齐饮食记录相关数据表。"""
    db_path = Path(__file__).parent / "cat_care.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feeding_plans (
                id INTEGER PRIMARY KEY,
                cat_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE,
                food_type VARCHAR NOT NULL,
                brand VARCHAR,
                product_name VARCHAR NOT NULL,
                life_stage VARCHAR,
                complete_balance_status VARCHAR NOT NULL DEFAULT 'pending',
                daily_amount FLOAT,
                amount_unit VARCHAR,
                feeding_frequency VARCHAR,
                daily_calories FLOAT,
                hydration_strategy VARCHAR,
                notes TEXT,
                sync_group_id VARCHAR,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(cat_id) REFERENCES cats(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS food_transition_plans (
                id INTEGER PRIMARY KEY,
                cat_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                start_date DATE NOT NULL,
                planned_days INTEGER NOT NULL DEFAULT 7,
                old_food_name VARCHAR NOT NULL,
                new_food_name VARCHAR NOT NULL,
                reason VARCHAR,
                status VARCHAR NOT NULL DEFAULT 'planned',
                end_date DATE,
                stop_reason TEXT,
                observation_notes TEXT,
                sync_group_id VARCHAR,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(cat_id) REFERENCES cats(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS food_transition_steps (
                id INTEGER PRIMARY KEY,
                transition_plan_id INTEGER NOT NULL,
                day_index INTEGER NOT NULL,
                old_food_ratio INTEGER NOT NULL,
                new_food_ratio INTEGER NOT NULL,
                notes TEXT,
                created_at DATETIME,
                FOREIGN KEY(transition_plan_id) REFERENCES food_transition_plans(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS supplement_courses (
                id INTEGER PRIMARY KEY,
                cat_id INTEGER NOT NULL,
                product_name VARCHAR NOT NULL,
                category VARCHAR,
                purpose VARCHAR,
                start_date DATE NOT NULL,
                end_date DATE,
                frequency VARCHAR,
                dosage FLOAT,
                dosage_unit VARCHAR,
                feeding_method VARCHAR,
                source VARCHAR,
                response VARCHAR,
                risk_notes TEXT,
                sync_group_id VARCHAR,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(cat_id) REFERENCES cats(id)
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS feeding_records (
                id INTEGER PRIMARY KEY,
                cat_id INTEGER NOT NULL,
                plan_id INTEGER,
                transition_plan_id INTEGER,
                recorded_at DATETIME NOT NULL,
                record_type VARCHAR NOT NULL,
                brand VARCHAR,
                item_name VARCHAR NOT NULL,
                flavor VARCHAR,
                amount FLOAT,
                amount_unit VARCHAR,
                calories FLOAT,
                consumed_status VARCHAR DEFAULT 'finished',
                feeding_method VARCHAR,
                notes TEXT,
                reaction VARCHAR DEFAULT 'none',
                sync_group_id VARCHAR,
                created_at DATETIME,
                updated_at DATETIME,
                FOREIGN KEY(cat_id) REFERENCES cats(id),
                FOREIGN KEY(plan_id) REFERENCES feeding_plans(id),
                FOREIGN KEY(transition_plan_id) REFERENCES food_transition_plans(id)
            )
            """
        )
        for table_name in ("feeding_plans", "food_transition_plans", "supplement_courses", "feeding_records"):
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            if "sync_group_id" not in existing_columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN sync_group_id VARCHAR")
        conn.commit()
    finally:
        conn.close()


ensure_feeding_schema()


def backfill_photo_tags() -> None:
    """把历史单猫照片补成标签关系，兼容新的多猫相册逻辑。"""
    db = SessionLocal()
    try:
        existing_pairs = {
            (photo_id, cat_id)
            for photo_id, cat_id in db.query(models.PhotoCatTag.photo_id, models.PhotoCatTag.cat_id).all()
        }

        photos_without_tags = (
            db.query(models.Photo.id, models.Photo.cat_id)
            .filter(models.Photo.cat_id.isnot(None))
            .all()
        )

        created = False
        for photo_id, cat_id in photos_without_tags:
            if (photo_id, cat_id) in existing_pairs:
                continue
            db.add(models.PhotoCatTag(photo_id=photo_id, cat_id=cat_id))
            created = True

        if created:
            db.commit()
    finally:
        db.close()


backfill_photo_tags()


def backfill_photo_metadata() -> None:
    """补齐历史照片的拍摄时间、内容指纹和全局排序。"""
    db = SessionLocal()
    try:
        photos_with_cat = (
            db.query(models.Photo)
            .options(joinedload(models.Photo.cat))
            .order_by(models.Photo.created_at.desc(), models.Photo.id.desc())
            .all()
        )

        changed = False
        owner_buckets: dict[int, list[models.Photo]] = {}

        for photo in photos_with_cat:
            if not photo.cat:
                continue

            photo_path = Path(__file__).parent / Path(photo.url.lstrip("/"))
            thumbnail_name = Path(photo.thumbnail).name if photo.thumbnail else f"thumb_{Path(photo.url).name}"
            thumbnail_path = Path(__file__).parent / "static" / "thumbnails" / thumbnail_name
            content = None
            if photo_path.exists():
                content = photo_path.read_bytes()

            if content and not photo.file_hash:
                photo.file_hash = compute_file_hash(content)
                changed = True

            if content:
                captured_from_thumbnail = save_thumbnail(content, thumbnail_path)
                thumbnail_url = f"/static/thumbnails/{thumbnail_name}"
                if photo.thumbnail != thumbnail_url:
                    photo.thumbnail = thumbnail_url
                    changed = True
            else:
                captured_from_thumbnail = None

            if content and not photo.captured_at:
                captured_at = captured_from_thumbnail or extract_captured_at(content)
                if captured_at:
                    photo.captured_at = captured_at
                    changed = True

            owner_buckets.setdefault(photo.cat.owner_id, []).append(photo)

        for owner_id, owner_photos in owner_buckets.items():
            owner_photos.sort(
                key=lambda item: (
                    -(item.captured_at or item.created_at).timestamp() if (item.captured_at or item.created_at) else 0,
                    -item.id,
                )
            )
            for index, photo in enumerate(owner_photos):
                if photo.sort_order is None or photo.sort_order == 0:
                    photo.sort_order = float(index)
                    changed = True

        if changed:
            db.commit()
    finally:
        db.close()


backfill_photo_metadata()

app = FastAPI(title="猫咪成长健康管理系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cats.router)
app.include_router(weights.router)
app.include_router(medical_history.router)
app.include_router(photos.router)
app.include_router(albums.router)
app.include_router(feeding.router)

# 挂载静态文件目录（用于头像等）
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# 挂载缩略图目录
thumbnails_dir = Path(__file__).parent / "static" / "thumbnails"
thumbnails_dir.mkdir(parents=True, exist_ok=True)

@app.get("/")
def root():
    return {"message": "猫咪成长健康管理系统 API"}

# 导入初始数据
from init_data import init_data
init_data()
