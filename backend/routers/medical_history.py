from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List

router = APIRouter(prefix="/api", tags=["medical_history"])

@router.get("/cats/{cat_id}/medical-history", response_model=List[schemas.MedicalHistory])
def get_medical_histories(cat_id: int, db: Session = Depends(get_db)):
    """获取猫咪的病史记录列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return db.query(models.MedicalHistory).filter(
        models.MedicalHistory.cat_id == cat_id
    ).order_by(models.MedicalHistory.date.desc()).all()

@router.post("/cats/{cat_id}/medical-history", response_model=schemas.MedicalHistory)
def create_medical_history(cat_id: int, medical: schemas.MedicalHistoryCreate, db: Session = Depends(get_db)):
    """创建病史记录"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    new_record = models.MedicalHistory(**medical.model_dump(), cat_id=cat_id)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

@router.get("/medical-history/{record_id}", response_model=schemas.MedicalHistory)
def get_medical_history(record_id: int, db: Session = Depends(get_db)):
    """获取单条病史记录"""
    record = db.query(models.MedicalHistory).filter(models.MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="病史记录不存在")
    return record

@router.put("/medical-history/{record_id}", response_model=schemas.MedicalHistory)
def update_medical_history(record_id: int, medical: schemas.MedicalHistoryUpdate, db: Session = Depends(get_db)):
    """更新病史记录"""
    record = db.query(models.MedicalHistory).filter(models.MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="病史记录不存在")
    update_data = medical.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return record

@router.delete("/medical-history/{record_id}")
def delete_medical_history(record_id: int, db: Session = Depends(get_db)):
    """删除病史记录"""
    record = db.query(models.MedicalHistory).filter(models.MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="病史记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}
