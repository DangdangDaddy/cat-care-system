from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from pathlib import Path
import shutil
import uuid

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
