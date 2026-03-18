from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List

router = APIRouter(prefix="/api", tags=["albums"])

@router.get("/cats/{cat_id}/albums", response_model=List[schemas.Album])
def get_albums(cat_id: int, db: Session = Depends(get_db)):
    """获取猫咪的相册列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return db.query(models.Album).filter(models.Album.cat_id == cat_id).all()

@router.post("/cats/{cat_id}/albums", response_model=schemas.Album)
def create_album(cat_id: int, album: schemas.AlbumCreate, db: Session = Depends(get_db)):
    """创建相册"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    
    # 验证封面照片存在且属于该猫咪
    if album.cover_photo_id:
        photo = db.query(models.Photo).filter(
            models.Photo.id == album.cover_photo_id,
            models.Photo.cat_id == cat_id
        ).first()
        if not photo:
            raise HTTPException(status_code=404, detail="封面照片不存在")
    
    new_album = models.Album(**album.model_dump(), cat_id=cat_id)
    db.add(new_album)
    db.commit()
    db.refresh(new_album)
    return new_album

@router.get("/albums/{album_id}", response_model=schemas.AlbumWithPhotos)
def get_album(album_id: int, db: Session = Depends(get_db)):
    """获取单个相册详情（包含照片）"""
    album = db.query(models.Album).filter(models.Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    return album

@router.put("/albums/{album_id}", response_model=schemas.Album)
def update_album(album_id: int, album_update: schemas.AlbumUpdate, db: Session = Depends(get_db)):
    """更新相册信息"""
    album = db.query(models.Album).filter(models.Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    update_data = album_update.model_dump(exclude_unset=True)
    
    # 验证封面照片
    if "cover_photo_id" in update_data and update_data["cover_photo_id"]:
        photo = db.query(models.Photo).filter(
            models.Photo.id == update_data["cover_photo_id"],
            models.Photo.cat_id == album.cat_id
        ).first()
        if not photo:
            raise HTTPException(status_code=404, detail="封面照片不存在")
    
    for key, value in update_data.items():
        setattr(album, key, value)
    db.commit()
    db.refresh(album)
    return album

@router.delete("/albums/{album_id}")
def delete_album(album_id: int, db: Session = Depends(get_db)):
    """删除相册（同时删除其中的照片）"""
    album = db.query(models.Album).filter(models.Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    db.delete(album)
    db.commit()
    return {"message": "删除成功"}

@router.post("/albums/{album_id}/photos/{photo_id}")
def add_photo_to_album(album_id: int, photo_id: int, db: Session = Depends(get_db)):
    """将照片添加到相册"""
    album = db.query(models.Album).filter(models.Album.id == album_id).first()
    if not album:
        raise HTTPException(status_code=404, detail="相册不存在")
    
    photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不存在")
    
    # 验证照片和相册属于同一只猫
    if photo.cat_id != album.cat_id:
        raise HTTPException(status_code=400, detail="照片和相册不属于同一只猫")
    
    photo.album_id = album_id
    db.commit()
    return {"message": "添加成功"}

@router.delete("/albums/{album_id}/photos/{photo_id}")
def remove_photo_from_album(album_id: int, photo_id: int, db: Session = Depends(get_db)):
    """从相册中移除照片（照片保留但不属于任何相册）"""
    photo = db.query(models.Photo).filter(
        models.Photo.id == photo_id,
        models.Photo.album_id == album_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="照片不在该相册中")
    
    photo.album_id = None
    db.commit()
    return {"message": "移除成功"}
