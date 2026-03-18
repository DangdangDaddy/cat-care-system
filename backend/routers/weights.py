from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api", tags=["weights"])

@router.get("/cats/{cat_id}/weights", response_model=list[schemas.WeightRecord])
def get_weights(cat_id: int, db: Session = Depends(get_db)):
    """获取猫咪的体重记录列表"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return db.query(models.WeightRecord).filter(
        models.WeightRecord.cat_id == cat_id
    ).order_by(models.WeightRecord.date).all()

@router.post("/cats/{cat_id}/weights", response_model=schemas.WeightRecord)
def add_weight(cat_id: int, weight: schemas.WeightRecordCreate, db: Session = Depends(get_db)):
    """添加体重记录"""
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    new_weight = models.WeightRecord(**weight.model_dump(), cat_id=cat_id)
    db.add(new_weight)
    db.commit()
    db.refresh(new_weight)
    return new_weight

@router.get("/weights/{weight_id}", response_model=schemas.WeightRecord)
def get_weight(weight_id: int, db: Session = Depends(get_db)):
    """获取单条体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    return weight

@router.put("/weights/{weight_id}", response_model=schemas.WeightRecord)
def update_weight(weight_id: int, weight_update: schemas.WeightRecordUpdate, db: Session = Depends(get_db)):
    """更新体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    update_data = weight_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(weight, key, value)
    db.commit()
    db.refresh(weight)
    return weight

@router.delete("/weights/{weight_id}")
def delete_weight(weight_id: int, db: Session = Depends(get_db)):
    """删除体重记录"""
    weight = db.query(models.WeightRecord).filter(models.WeightRecord.id == weight_id).first()
    if not weight:
        raise HTTPException(status_code=404, detail="体重记录不存在")
    db.delete(weight)
    db.commit()
    return {"message": "删除成功"}

@router.get("/weights/chart")
def get_chart_data(user_id: int, db: Session = Depends(get_db)):
    """获取用户的猫咪体重图表数据"""
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()
    result = []
    for cat in cats:
        weights = db.query(models.WeightRecord).filter(
            models.WeightRecord.cat_id == cat.id
        ).order_by(models.WeightRecord.date).all()
        result.append({
            "cat_id": cat.id,
            "cat_name": cat.name,
            "data": [{"date": str(w.date), "weight": w.weight} for w in weights]
        })
    return result
