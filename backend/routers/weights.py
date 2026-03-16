from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

router = APIRouter(prefix="/api", tags=["weights"])

@router.get("/cats/{cat_id}/weights", response_model=list[schemas.WeightRecord])
def get_weights(cat_id: int, db: Session = Depends(get_db)):
    return db.query(models.WeightRecord).filter(models.WeightRecord.cat_id == cat_id).order_by(models.WeightRecord.date).all()

@router.post("/cats/{cat_id}/weights", response_model=schemas.WeightRecord)
def add_weight(cat_id: int, weight: schemas.WeightRecordCreate, db: Session = Depends(get_db)):
    new_weight = models.WeightRecord(**weight.model_dump(), cat_id=cat_id)
    db.add(new_weight)
    db.commit()
    db.refresh(new_weight)
    return new_weight

@router.get("/weights/chart")
def get_chart_data(user_id: int, db: Session = Depends(get_db)):
    cats = db.query(models.Cat).filter(models.Cat.owner_id == user_id).all()
    result = []
    for cat in cats:
        weights = db.query(models.WeightRecord).filter(models.WeightRecord.cat_id == cat.id).order_by(models.WeightRecord.date).all()
        result.append({
            "cat_id": cat.id,
            "cat_name": cat.name,
            "data": [{"date": str(w.date), "weight": w.weight} for w in weights]
        })
    return result
