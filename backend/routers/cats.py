from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database import get_db
import models, schemas
from pathlib import Path
import shutil
import uuid
from typing import List, Optional

router = APIRouter(prefix="/api/cats", tags=["cats"])

# 头像存储目录
AVATAR_DIR = Path(__file__).parent.parent / "static" / "avatars"
AVATAR_DIR.mkdir(parents=True, exist_ok=True)

@router.get("/", response_model=list[schemas.Cat])
def get_cats(user_id: int, db: Session = Depends(get_db)):
    return db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()

@router.post("/", response_model=schemas.Cat)
def create_cat(cat: schemas.CatCreate, user_id: int, db: Session = Depends(get_db)):
    new_cat = models.Cat(**cat.model_dump(), owner_id=user_id)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat


# 固定路径必须放在 /{cat_id} 前面，避免 FastAPI 把 search 解析成 cat_id。
@router.post("/batch-delete")
def batch_delete_cats(
    cat_ids: Optional[List[int]] = Query(None, description="要删除的猫咪ID列表"),
    user_id: int = Query(..., description="用户ID"),
    db: Session = Depends(get_db)
):
    """批量删除猫咪

    采用部分成功模式：即使部分删除失败，成功的部分也会保存。
    """
    unique_cat_ids = []
    for cat_id in cat_ids or []:
        if cat_id not in unique_cat_ids:
            unique_cat_ids.append(cat_id)

    if not unique_cat_ids:
        raise HTTPException(status_code=400, detail="请提供要删除的猫咪ID")

    if len(unique_cat_ids) > 50:
        raise HTTPException(status_code=400, detail="一次最多删除50只猫咪")

    success_ids = []
    failed_items = []

    for cat_id in unique_cat_ids:
        try:
            db_cat = db.query(models.Cat).filter(
                models.Cat.id == cat_id,
                models.Cat.owner_id == user_id
            ).first()

            if not db_cat:
                failed_items.append({"cat_id": cat_id, "reason": "猫咪不存在或无权限"})
                continue

            db.delete(db_cat)
            success_ids.append(cat_id)
        except Exception as e:
            failed_items.append({"cat_id": cat_id, "reason": str(e)})

    db.commit()

    return {
        "success": True,
        "message": f"成功删除 {len(success_ids)} 只猫咪",
        "success_count": len(success_ids),
        "failed_count": len(failed_items),
        "success_ids": success_ids,
        "failed_items": failed_items
    }


@router.get("/search", response_model=List[schemas.Cat])
def search_cats(
    user_id: int = Query(..., description="用户ID"),
    keyword: Optional[str] = Query(None, description="搜索关键词（名字、品种、毛色）"),
    breed: Optional[str] = Query(None, description="品种筛选"),
    gender: Optional[str] = Query(None, description="性别筛选 (male/female)"),
    neutered: Optional[bool] = Query(None, description="绝育状态筛选"),
    db: Session = Depends(get_db)
):
    """搜索猫咪

    支持关键词搜索（名字、品种、毛色）和多条件筛选。
    """
    query = db.query(models.Cat).filter(models.Cat.owner_id == user_id)

    if keyword:
        search_pattern = f"%{keyword}%"
        query = query.filter(
            or_(
                models.Cat.name.ilike(search_pattern),
                models.Cat.breed.ilike(search_pattern),
                models.Cat.color.ilike(search_pattern)
            )
        )

    if breed:
        query = query.filter(models.Cat.breed == breed)

    if gender:
        query = query.filter(models.Cat.gender == gender)

    if neutered is not None:
        query = query.filter(models.Cat.neutered == neutered)

    return query.all()


@router.put("/{cat_id}", response_model=schemas.Cat)
def update_cat(cat_id: int, cat: schemas.CatUpdate, db: Session = Depends(get_db)):
    db_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    update_data = cat.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cat, key, value)
    db.commit()
    db.refresh(db_cat)
    return db_cat

@router.get("/{cat_id}", response_model=schemas.Cat)
def get_cat(cat_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return db_cat

@router.delete("/{cat_id}")
def delete_cat(cat_id: int, db: Session = Depends(get_db)):
    db_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    db.delete(db_cat)
    db.commit()
    return {"message": "删除成功"}

@router.post("/{cat_id}/avatar")
async def upload_avatar(cat_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """上传猫咪头像"""
    db_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    
    # 生成唯一文件名
    ext = Path(file.filename).suffix or ".jpg"
    filename = f"{cat_id}_{uuid.uuid4().hex}{ext}"
    file_path = AVATAR_DIR / filename
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 更新数据库
    url = f"/static/avatars/{filename}"
    db_cat.avatar = url
    db.commit()
    db.refresh(db_cat)
    
    return {"url": url}

@router.put("/{cat_id}/photos")
def update_photos(cat_id: int, photos_data: dict, db: Session = Depends(get_db)):
    """更新猫咪照片列表"""
    db_cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not db_cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    
    # 照片列表存储在 photos 关系中，这里简化处理
    # 实际应该操作 Photo 表
    return {"message": "更新成功"}
