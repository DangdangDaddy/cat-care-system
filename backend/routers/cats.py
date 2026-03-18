from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api/cats", tags=["cats"])

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
