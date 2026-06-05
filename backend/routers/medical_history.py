from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from typing import List
router = APIRouter(prefix="/api", tags=["medical_history"])


def annotate_sync_group_size(db: Session, records):
    """为健康记录补充真实的同步组成员数量。"""
    if not records:
        return records

    is_single_record = not isinstance(records, list)
    items = [records] if is_single_record else records

    group_ids = [record.sync_group_id for record in items if getattr(record, "sync_group_id", None)]
    counts = defaultdict(int)
    if group_ids:
        grouped_counts = (
            db.query(
                models.MedicalHistory.sync_group_id,
                models.MedicalHistory.id,
            )
            .filter(models.MedicalHistory.sync_group_id.in_(set(group_ids)))
            .all()
        )
        for group_id, _record_id in grouped_counts:
            if group_id:
                counts[group_id] += 1

    for record in items:
        group_id = getattr(record, "sync_group_id", None)
        setattr(record, "sync_group_size", counts.get(group_id, 0) if group_id else 0)

    return items[0] if is_single_record else items

@router.get("/cats/{cat_id}/medical-history", response_model=List[schemas.MedicalHistory])
def get_medical_histories(cat_id: int, db: Session = Depends(get_db)):
    """获取猫咪的病史记录列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    records = db.query(models.MedicalHistory).filter(
        models.MedicalHistory.cat_id == cat_id
    ).order_by(models.MedicalHistory.date.desc()).all()
    return annotate_sync_group_size(db, records)

@router.get("/medical-history/group/{group_id}", response_model=List[schemas.MedicalHistory])
def get_medical_histories_by_group(group_id: str, db: Session = Depends(get_db)):
    """获取同一同步组的记录"""
    records = db.query(models.MedicalHistory).filter(
        models.MedicalHistory.sync_group_id == group_id
    ).order_by(models.MedicalHistory.date.desc()).all()
    return annotate_sync_group_size(db, records)

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
    return annotate_sync_group_size(db, new_record)

@router.post("/cats/{cat_id}/medical-history/batch", response_model=List[schemas.MedicalHistory])
def create_medical_history_batch(cat_id: int, payload: dict, db: Session = Depends(get_db)):
    """批量创建同步健康记录"""
    cat_ids = payload.get("cat_ids") or []
    medical_data = payload.get("medical")
    if not isinstance(cat_ids, list) or not cat_ids:
        raise HTTPException(status_code=400, detail="请至少选择一只猫咪")
    if not isinstance(medical_data, dict):
        raise HTTPException(status_code=400, detail="健康记录数据无效")

    valid_cat_ids = []
    for cid in cat_ids:
        cat = db.query(models.Cat).filter(models.Cat.id == int(cid)).first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"猫咪不存在: {cid}")
        valid_cat_ids.append(int(cid))

    medical_obj = schemas.MedicalHistoryCreate(**medical_data)
    created = []
    for cid in valid_cat_ids:
        new_record = models.MedicalHistory(**medical_obj.model_dump(), cat_id=cid)
        db.add(new_record)
        created.append(new_record)

    db.commit()
    for record in created:
        db.refresh(record)
    return annotate_sync_group_size(db, created)

@router.get("/medical-history/{record_id}", response_model=schemas.MedicalHistory)
def get_medical_history(record_id: int, db: Session = Depends(get_db)):
    """获取单条病史记录"""
    record = db.query(models.MedicalHistory).filter(models.MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="病史记录不存在")
    return annotate_sync_group_size(db, record)

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
    return annotate_sync_group_size(db, record)

@router.put("/medical-history/group/{group_id}", response_model=List[schemas.MedicalHistory])
def update_medical_history_group(group_id: str, medical: schemas.MedicalHistoryUpdate, db: Session = Depends(get_db)):
    """更新同一同步组的所有记录"""
    records = db.query(models.MedicalHistory).filter(models.MedicalHistory.sync_group_id == group_id).all()
    if not records:
        raise HTTPException(status_code=404, detail="同步组记录不存在")

    update_data = medical.model_dump(exclude_unset=True)
    for record in records:
        for key, value in update_data.items():
            setattr(record, key, value)
    db.commit()
    for record in records:
        db.refresh(record)
    return annotate_sync_group_size(db, records)

@router.delete("/medical-history/{record_id}")
def delete_medical_history(record_id: int, db: Session = Depends(get_db)):
    """删除病史记录"""
    record = db.query(models.MedicalHistory).filter(models.MedicalHistory.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="病史记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}
