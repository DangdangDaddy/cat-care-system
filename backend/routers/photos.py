from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session, joinedload
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from database import get_db
import models
import schemas
from photo_utils import (
    compute_average_hash_from_content,
    compute_file_hash,
    hamming_distance,
    load_average_hash_from_path,
    save_thumbnail,
)

router = APIRouter(prefix="/api", tags=["photos"])

# 照片存储目录
PHOTO_DIR = Path(__file__).parent.parent / "static" / "photos"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

# 缩略图目录
THUMBNAIL_DIR = Path(__file__).parent.parent / "static" / "thumbnails"
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)
SIMILAR_PHOTO_MAX_DISTANCE = 6

def save_upload_file(upload_filename: str, content: bytes, file_prefix: int) -> tuple[str, Optional[str], str, Optional[datetime]]:
    """保存上传的文件，生成缩略图，返回文件名和缩略图 URL。"""
    ext = Path(upload_filename or "").suffix or ".jpg"
    filename = f"{file_prefix}_{uuid.uuid4().hex}{ext}"
    file_path = PHOTO_DIR / filename

    with open(file_path, "wb") as buffer:
        buffer.write(content)

    thumbnail_filename = None
    captured_at = None
    try:
        thumbnail_filename = f"thumb_{filename}"
        thumbnail_path = THUMBNAIL_DIR / thumbnail_filename
        captured_at = save_thumbnail(content, thumbnail_path)
    except Exception as exc:
        print(f"缩略图生成失败: {exc}")
        thumbnail_filename = None

    thumbnail_url = f"/static/thumbnails/{thumbnail_filename}" if thumbnail_filename else None
    return filename, thumbnail_url, compute_file_hash(content), captured_at


def parse_tag_cat_ids(raw_value: Optional[str], fallback_cat_id: int) -> List[int]:
    """支持 JSON 数组或逗号分隔字符串。"""
    if not raw_value:
        return [fallback_cat_id]

    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            values = parsed
        else:
            values = [parsed]
    except json.JSONDecodeError:
        values = [item.strip() for item in raw_value.split(",")]

    cat_ids: List[int] = []
    for value in values:
        if value in (None, ""):
            continue
        cat_id = int(value)
        if cat_id not in cat_ids:
            cat_ids.append(cat_id)

    return cat_ids or [fallback_cat_id]


def serialize_photo(photo: models.Photo) -> dict:
    tagged_cats = []
    for tag in sorted(photo.tagged_cats, key=lambda item: item.cat_id):
        if tag.cat:
            tagged_cats.append(
                {
                    "id": tag.cat.id,
                    "name": tag.cat.name,
                    "avatar": tag.cat.avatar,
                }
            )

    return {
        "id": photo.id,
        "cat_id": photo.cat_id,
        "album_id": photo.album_id,
        "url": photo.url,
        "thumbnail": photo.thumbnail,
        "description": photo.description,
        "captured_at": photo.captured_at,
        "sort_order": photo.sort_order,
        "is_pinned": bool(photo.is_pinned),
        "created_at": photo.created_at,
        "cats": tagged_cats,
    }


def serialize_duplicate_photo_hint(photo: models.Photo) -> dict:
    return {
        "id": photo.id,
        "url": photo.url,
        "thumbnail": photo.thumbnail,
        "created_at": photo.created_at.isoformat() if photo.created_at else None,
        "captured_at": photo.captured_at.isoformat() if photo.captured_at else None,
        "cats": [
            {
                "id": tag.cat.id,
                "name": tag.cat.name,
                "avatar": tag.cat.avatar,
            }
            for tag in sorted(photo.tagged_cats, key=lambda item: item.cat_id)
            if tag.cat
        ],
    }


def serialize_similar_photo_hint(photo: models.Photo, distance: int) -> dict:
    payload = serialize_duplicate_photo_hint(photo)
    payload["distance"] = distance
    payload["confidence"] = round(max(0.4, 1 - (distance / 64)), 2)
    return payload


def apply_default_photo_order(query):
    """统一照片列表排序，保证详情页和 Dashboard 的照片顺序一致。"""
    return query.order_by(
        models.Photo.is_pinned.desc(),
        models.Photo.sort_order.asc(),
        models.Photo.created_at.desc(),
        models.Photo.id.desc(),
    )


def get_owner_photo_bounds(db: Session, owner_id: int) -> tuple[float, float]:
    owner_photos = (
        db.query(models.Photo.sort_order)
        .join(models.Cat, models.Cat.id == models.Photo.cat_id)
        .filter(models.Cat.owner_id == owner_id)
        .all()
    )
    values = [row[0] for row in owner_photos if row[0] is not None]
    if not values:
        return 0.0, 0.0
    return min(values), max(values)


def normalize_owner_photo_order(db: Session, owner_id: int) -> None:
    """压实排序值，避免反复拖拽后浮点间距过小。"""
    photos = (
        apply_default_photo_order(
            db.query(models.Photo)
            .join(models.Cat, models.Cat.id == models.Photo.cat_id)
            .filter(models.Cat.owner_id == owner_id)
        )
        .all()
    )
    for index, photo in enumerate(photos):
        photo.sort_order = float(index)


def calculate_new_sort_order(db: Session, owner_id: int, prev_photo_id: Optional[int], next_photo_id: Optional[int]) -> float:
    """用相邻照片的中间值完成拖拽排序，减少整表重排次数。"""
    prev_photo = None
    next_photo = None

    if prev_photo_id:
        prev_photo = (
            db.query(models.Photo)
            .join(models.Cat, models.Cat.id == models.Photo.cat_id)
            .filter(models.Photo.id == prev_photo_id, models.Cat.owner_id == owner_id)
            .first()
        )
    if next_photo_id:
        next_photo = (
            db.query(models.Photo)
            .join(models.Cat, models.Cat.id == models.Photo.cat_id)
            .filter(models.Photo.id == next_photo_id, models.Cat.owner_id == owner_id)
            .first()
        )

    if prev_photo and next_photo:
        gap = next_photo.sort_order - prev_photo.sort_order
        if abs(gap) < 1e-6:
            normalize_owner_photo_order(db, owner_id)
            db.flush()
            prev_photo = db.query(models.Photo).filter(models.Photo.id == prev_photo_id).first()
            next_photo = db.query(models.Photo).filter(models.Photo.id == next_photo_id).first()
        return (prev_photo.sort_order + next_photo.sort_order) / 2

    if prev_photo:
        _, max_sort = get_owner_photo_bounds(db, owner_id)
        return max(prev_photo.sort_order + 1, max_sort + 1)

    if next_photo:
        min_sort, _ = get_owner_photo_bounds(db, owner_id)
        return min(next_photo.sort_order - 1, min_sort - 1)

    return 0.0


def sync_photo_tags(db: Session, photo: models.Photo, tag_cat_ids: List[int]) -> None:
    """同步一张照片关联的猫咪标签。"""
    unique_ids: List[int] = []
    for cat_id in tag_cat_ids:
        if cat_id not in unique_ids:
            unique_ids.append(cat_id)

    if not unique_ids:
        raise HTTPException(status_code=400, detail="请至少保留一只猫咪标注")

    current_cat = db.query(models.Cat).filter(models.Cat.id == photo.cat_id).first()
    if not current_cat:
        raise HTTPException(status_code=404, detail="照片所属猫咪不存在")

    tagged_cats = db.query(models.Cat).filter(models.Cat.id.in_(unique_ids)).all()
    if len(tagged_cats) != len(unique_ids):
        raise HTTPException(status_code=400, detail="存在无效的猫咪标注")

    for tagged_cat in tagged_cats:
        if tagged_cat.owner_id != current_cat.owner_id:
            raise HTTPException(status_code=400, detail="只能标注当前用户自己的猫咪")

    db.query(models.PhotoCatTag).filter(models.PhotoCatTag.photo_id == photo.id).delete()
    db.flush()

    for cat_id in unique_ids:
        db.add(models.PhotoCatTag(photo_id=photo.id, cat_id=cat_id))

    photo.cat_id = unique_ids[0]


def load_photo_with_tags(db: Session, photo_id: int) -> Optional[models.Photo]:
    return (
        db.query(models.Photo)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .filter(models.Photo.id == photo_id)
        .first()
    )


def remove_photo_files(photo: models.Photo) -> None:
    if photo.url:
        file_path = PHOTO_DIR / Path(photo.url).name
        if file_path.exists():
            file_path.unlink()

    if photo.thumbnail:
        thumbnail_path = THUMBNAIL_DIR / Path(photo.thumbnail).name
        if thumbnail_path.exists():
            thumbnail_path.unlink()


def find_similar_photo(
    db: Session,
    owner_id: int,
    content: bytes,
    exclude_file_hash: Optional[str] = None,
) -> Optional[dict]:
    """基于感知哈希找近似图片，避免同一张照片被轻微裁切后重复上传。"""
    target_hash = compute_average_hash_from_content(content)
    if target_hash is None:
        return None

    candidate_photos = (
        db.query(models.Photo)
        .join(models.Cat, models.Cat.id == models.Photo.cat_id)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .filter(models.Cat.owner_id == owner_id)
        .all()
    )

    best_match = None
    for photo in candidate_photos:
        if exclude_file_hash and photo.file_hash == exclude_file_hash:
            continue

        photo_source = photo.thumbnail or photo.url
        photo_path = THUMBNAIL_DIR / Path(photo_source).name if photo.thumbnail else PHOTO_DIR / Path(photo_source).name
        photo_hash = load_average_hash_from_path(photo_path)
        if photo_hash is None:
            continue

        distance = hamming_distance(target_hash, photo_hash)
        if distance > SIMILAR_PHOTO_MAX_DISTANCE:
            continue

        if (
            best_match is None
            or distance < best_match["distance"]
            or (distance == best_match["distance"] and photo.id > best_match["photo"].id)
        ):
            best_match = {"photo": photo, "distance": distance}

    return best_match


@router.post("/cats/{cat_id}/photos", response_model=schemas.Photo)
async def upload_photo(
    cat_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    album_id: Optional[int] = Form(None),
    tag_cat_ids: Optional[str] = Form(None),
    allow_duplicate: bool = Form(False),
    allow_similar: bool = Form(False),
    db: Session = Depends(get_db),
):
    """上传照片并标注这张照片里出现了哪些猫。"""
    current_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not current_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="文件内容为空")

    file_hash = compute_file_hash(content)
    duplicate_photo = (
        db.query(models.Photo)
        .join(models.Cat, models.Cat.id == models.Photo.cat_id)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .filter(models.Cat.owner_id == current_cat.owner_id, models.Photo.file_hash == file_hash)
        .first()
    )
    if duplicate_photo and not allow_duplicate:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "duplicate_photo",
                "message": "检测到重复照片",
                "duplicate_photo": serialize_duplicate_photo_hint(duplicate_photo),
            },
        )

    similar_photo = find_similar_photo(
        db,
        current_cat.owner_id,
        content,
        exclude_file_hash=file_hash,
    )
    if similar_photo and not allow_similar:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "similar_photo",
                "message": "检测到相似照片",
                "similar_photo": serialize_similar_photo_hint(
                    similar_photo["photo"],
                    similar_photo["distance"],
                ),
            },
        )

    selected_cat_ids = parse_tag_cat_ids(tag_cat_ids, cat_id)
    tagged_cats = (
        db.query(models.Cat)
        .filter(models.Cat.id.in_(selected_cat_ids))
        .all()
    )
    if len(tagged_cats) != len(selected_cat_ids):
        raise HTTPException(status_code=400, detail="存在无效的猫咪标注")

    for tagged_cat in tagged_cats:
        if tagged_cat.owner_id != current_cat.owner_id:
            raise HTTPException(status_code=400, detail="只能标注当前用户自己的猫咪")

    primary_cat_id = selected_cat_ids[0]

    if album_id:
        album = (
            db.query(models.Album)
            .filter(models.Album.id == album_id, models.Album.cat_id == primary_cat_id)
            .first()
        )
        if not album:
            raise HTTPException(status_code=404, detail="相册不存在")

    filename, thumbnail, stored_hash, captured_at = save_upload_file(file.filename or "", content, cat_id)
    url = f"/static/photos/{filename}"

    owner_min_sort, _ = get_owner_photo_bounds(db, current_cat.owner_id)
    photo = models.Photo(
        cat_id=primary_cat_id,
        album_id=album_id,
        url=url,
        thumbnail=thumbnail,
        description=description,
        file_hash=stored_hash,
        captured_at=captured_at,
        sort_order=owner_min_sort - 1 if owner_min_sort is not None else 0,
    )
    db.add(photo)
    db.flush()

    for tagged_cat_id in selected_cat_ids:
        db.add(models.PhotoCatTag(photo_id=photo.id, cat_id=tagged_cat_id))

    db.commit()
    photo = load_photo_with_tags(db, photo.id)
    return serialize_photo(photo)


@router.get("/cats/{cat_id}/photos", response_model=List[schemas.Photo])
def get_photos(cat_id: int, album_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取某只猫相册中的照片，支持合照在多只猫详情页重复出现。"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")

    query = (
        db.query(models.Photo)
        .join(models.PhotoCatTag, models.PhotoCatTag.photo_id == models.Photo.id)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .filter(models.PhotoCatTag.cat_id == cat_id)
        .distinct()
    )
    if album_id:
        query = query.filter(models.Photo.album_id == album_id)

    photos = apply_default_photo_order(query).all()
    return [serialize_photo(photo) for photo in photos]


@router.get("/photos/all", response_model=List[schemas.Photo])
def get_all_photos(user_id: int = Query(...), db: Session = Depends(get_db)):
    """Dashboard 相册用，按照片去重返回当前用户的所有照片。"""
    photos = apply_default_photo_order(
        db.query(models.Photo)
        .join(models.PhotoCatTag, models.PhotoCatTag.photo_id == models.Photo.id)
        .join(models.Cat, models.Cat.id == models.PhotoCatTag.cat_id)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .filter(models.Cat.owner_id == user_id)
        .distinct()
    ).all()
    return [serialize_photo(photo) for photo in photos]


@router.get("/photos/{photo_id}", response_model=schemas.Photo)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    photo = load_photo_with_tags(db, photo_id)
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return serialize_photo(photo)


@router.post("/photos/recommend-tags", response_model=schemas.PhotoTagRecommendationResponse)
async def recommend_photo_tags(
    file: UploadFile = File(...),
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    """
    第二阶段的轻量入口：基于已标注图片的感知哈希做相似度推荐。
    """
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).order_by(models.Cat.id.asc()).all()
    if not cats:
        return {"recommendations": []}

    content = await file.read()
    if not content:
        return {"recommendations": []}

    try:
        target_hash = compute_average_hash_from_content(content)
    except Exception:
        return {"recommendations": []}
    if target_hash is None:
        return {"recommendations": []}

    candidate_photos = (
        db.query(models.Photo)
        .options(joinedload(models.Photo.tagged_cats).joinedload(models.PhotoCatTag.cat))
        .all()
    )

    best_matches: dict[int, dict] = {}
    for photo in candidate_photos:
        if len(photo.tagged_cats) != 1:
            continue

        tagged_cat = photo.tagged_cats[0].cat
        if not tagged_cat or tagged_cat.owner_id != user_id:
            continue

        photo_source = photo.thumbnail or photo.url
        photo_path = THUMBNAIL_DIR / Path(photo_source).name if photo.thumbnail else PHOTO_DIR / Path(photo_source).name
        photo_hash = load_average_hash_from_path(photo_path)
        if photo_hash is None:
            continue

        distance = hamming_distance(target_hash, photo_hash)
        confidence = round(max(0.4, 1 - (distance / 64)), 2)

        current = best_matches.get(tagged_cat.id)
        if not current or confidence > current["confidence"]:
            best_matches[tagged_cat.id] = {
                "cat_id": tagged_cat.id,
                "cat_name": tagged_cat.name,
                "confidence": confidence,
            }

    recommendations = sorted(best_matches.values(), key=lambda item: item["confidence"], reverse=True)
    recommendations = [item for item in recommendations if item["confidence"] >= 0.55][:3]
    return {"recommendations": recommendations}


@router.put("/photos/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: int, photo_update: schemas.PhotoUpdate, db: Session = Depends(get_db)):
    """更新照片信息（描述、相册、照片里的猫）。"""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    update_data = photo_update.model_dump(exclude_unset=True)
    if "album_id" in update_data and update_data["album_id"]:
        album = (
            db.query(models.Album)
            .filter(models.Album.id == update_data["album_id"], models.Album.cat_id == photo.cat_id)
            .first()
        )
        if not album:
            raise HTTPException(status_code=404, detail="相册不存在")

    for key, value in update_data.items():
        if key == "tag_cat_ids":
            continue
        setattr(photo, key, value)

    tag_cat_ids = update_data.get("tag_cat_ids")
    if tag_cat_ids is not None:
        sync_photo_tags(db, photo, tag_cat_ids)

    db.commit()
    photo = load_photo_with_tags(db, photo_id)
    return serialize_photo(photo)


@router.post("/photos/reorder")
def reorder_photos(payload: schemas.PhotoReorderRequest, db: Session = Depends(get_db)):
    """更新照片的全局手动排序。"""
    photo = (
        db.query(models.Photo)
        .join(models.Cat, models.Cat.id == models.Photo.cat_id)
        .filter(models.Photo.id == payload.photo_id, models.Cat.owner_id == payload.user_id)
        .first()
    )
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    new_sort_order = calculate_new_sort_order(db, payload.user_id, payload.prev_photo_id, payload.next_photo_id)
    photo.sort_order = new_sort_order
    db.commit()
    db.refresh(photo)
    photo = load_photo_with_tags(db, photo.id)
    return serialize_photo(photo)


@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, cat_id: Optional[int] = None, db: Session = Depends(get_db)):
    """删除照片；若传入 cat_id，则只从当前猫咪相册移除这张照片。"""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")

    if cat_id is None:
        remove_photo_files(photo)
        db.delete(photo)
        db.commit()
        return {"message": "照片已删除"}

    tag = (
        db.query(models.PhotoCatTag)
        .filter(models.PhotoCatTag.photo_id == photo_id, models.PhotoCatTag.cat_id == cat_id)
        .first()
    )
    if not tag:
        raise HTTPException(status_code=404, detail="照片不在当前猫咪相册中")

    db.delete(tag)
    db.flush()

    remaining_tags = (
        db.query(models.PhotoCatTag)
        .filter(models.PhotoCatTag.photo_id == photo_id)
        .order_by(models.PhotoCatTag.cat_id.asc())
        .all()
    )

    if not remaining_tags:
        remove_photo_files(photo)
        db.delete(photo)
        db.commit()
        return {"message": "照片已删除"}

    if photo.cat_id == cat_id:
        photo.cat_id = remaining_tags[0].cat_id

    db.commit()
    return {
        "message": "已从当前猫咪相册移除",
        "remaining_cat_ids": [tag_item.cat_id for tag_item in remaining_tags],
    }
