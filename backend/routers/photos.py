from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List, Optional
from pathlib import Path
import shutil
import uuid
from datetime import datetime

router = APIRouter(prefix="/api", tags=["photos"])

# 照片存储目录
PHOTO_DIR = Path(__file__).parent.parent / "static" / "photos"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)

def save_upload_file(upload_file: UploadFile, cat_id: int) -> tuple[str, str]:
    """保存上传的文件，返回文件名和缩略图文件名"""
    # 生成唯一文件名
    ext = Path(upload_file.filename).suffix or ".jpg"
    filename = f"{cat_id}_{uuid.uuid4().hex}{ext}"
    file_path = PHOTO_DIR / filename
    
    # 保存文件
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    
    # TODO: 生成缩略图（可以后续使用 Pillow 实现）
    thumbnail = None  # 暂时使用原图
    
    return filename, thumbnail

@router.post("/cats/{cat_id}/photos", response_model=schemas.Photo)
async def upload_photo(
    cat_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    album_id: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """上传照片"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    
    # 验证相册存在且属于该猫咪
    if album_id:
        album = db.query(models.Album).filter(
            models.Album.id == album_id,
            models.Album.cat_id == cat_id
        ).first()
        if not album:
            raise HTTPException(status_code=404, detail="相册不存在")
    
    # 保存文件
    filename, thumbnail = save_upload_file(file, cat_id)
    
    # 创建数据库记录
    url = f"/static/photos/{filename}"
    photo = models.Photo(
        cat_id=cat_id,
        album_id=album_id,
        url=url,
        thumbnail=thumbnail,
        description=description
    )
    db.add(photo)
    db.commit()
    db.refresh(photo)
    return photo

@router.get("/cats/{cat_id}/photos", response_model=List[schemas.Photo])
def get_photos(cat_id: int, album_id: Optional[int] = None, db: Session = Depends(get_db)):
    """获取猫咪的照片列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    
    query = db.query(models.Photo).filter(models.Photo.cat_id == cat_id)
    if album_id:
        query = query.filter(models.Photo.album_id == album_id)
    
    return query.order_by(models.Photo.created_at.desc()).all()

@router.get("/photos/{photo_id}", response_model=schemas.Photo)
def get_photo(photo_id: int, db: Session = Depends(get_db)):
    """获取单张照片详情"""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    return photo

@router.put("/photos/{photo_id}", response_model=schemas.Photo)
def update_photo(photo_id: int, photo_update: schemas.PhotoUpdate, db: Session = Depends(get_db)):
    """更新照片信息（描述、相册）"""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    update_data = photo_update.model_dump(exclude_unset=True)
    
    # 验证相册
    if "album_id" in update_data and update_data["album_id"]:
        album = db.query(models.Album).filter(
            models.Album.id == update_data["album_id"],
            models.Album.cat_id == photo.cat_id
        ).first()
        if not album:
            raise HTTPException(status_code=404, detail="相册不存在")
    
    for key, value in update_data.items():
        setattr(photo, key, value)
    db.commit()
    db.refresh(photo)
    return photo

@router.delete("/photos/{photo_id}")
def delete_photo(photo_id: int, db: Session = Depends(get_db)):
    """删除照片"""
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 删除文件
    if photo.url:
        file_path = PHOTO_DIR / Path(photo.url).name
        if file_path.exists():
            file_path.unlink()
    
    db.delete(photo)
    db.commit()
    return {"message": "删除成功"}
