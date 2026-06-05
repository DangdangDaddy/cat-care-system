from collections import defaultdict
from datetime import datetime, time
from typing import Any, List, Optional, Type

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from database import get_db
import models
import schemas


router = APIRouter(prefix="/api", tags=["feeding"])


def ensure_cat_exists(cat_id: int, db: Session) -> models.Cat:
    cat = db.query(models.Cat).filter(models.Cat.id == cat_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="猫咪不存在")
    return cat


def validate_cat_ids(cat_ids: List[int], db: Session) -> List[int]:
    if not isinstance(cat_ids, list) or not cat_ids:
        raise HTTPException(status_code=400, detail="请至少选择一只猫咪")

    valid_cat_ids: List[int] = []
    for raw_cat_id in cat_ids:
        cat = db.query(models.Cat).filter(models.Cat.id == int(raw_cat_id)).first()
        if not cat:
            raise HTTPException(status_code=404, detail=f"猫咪不存在: {raw_cat_id}")
        valid_cat_id = int(raw_cat_id)
        if valid_cat_id not in valid_cat_ids:
            valid_cat_ids.append(valid_cat_id)
    return valid_cat_ids


def annotate_sync_group_size(db: Session, records, model_cls: Type[Any]):
    """为饮食记录相关对象补充同步组成员数量。"""
    if not records:
        return records

    is_single_record = not isinstance(records, list)
    items = [records] if is_single_record else records

    group_ids = [record.sync_group_id for record in items if getattr(record, "sync_group_id", None)]
    counts = defaultdict(int)
    if group_ids:
        grouped_counts = (
            db.query(model_cls.sync_group_id, model_cls.id)
            .filter(model_cls.sync_group_id.in_(set(group_ids)))
            .all()
        )
        for group_id, _record_id in grouped_counts:
            if group_id:
                counts[group_id] += 1

    for record in items:
        group_id = getattr(record, "sync_group_id", None)
        setattr(record, "sync_group_size", counts.get(group_id, 0) if group_id else 0)

    return items[0] if is_single_record else items


def get_transition_templates(days: int) -> List[schemas.FoodTransitionStepCreate]:
    """按计划天数生成默认换粮比例，兼容 7 日法和更慢的敏感肠胃方案。"""
    if days <= 7:
        ratios = [(1, 75, 25), (2, 75, 25), (3, 50, 50), (4, 50, 50), (5, 25, 75), (6, 25, 75), (7, 0, 100)]
    elif days <= 10:
        ratios = [(1, 80, 20), (3, 60, 40), (5, 50, 50), (7, 25, 75), (9, 10, 90), (10, 0, 100)]
    else:
        ratios = [(1, 90, 10), (4, 75, 25), (7, 60, 40), (10, 50, 50), (13, 30, 70), (16, 10, 90), (days, 0, 100)]

    steps = []
    for day_index, old_ratio, new_ratio in ratios:
        if day_index <= days:
            steps.append(
                schemas.FoodTransitionStepCreate(
                    day_index=day_index,
                    old_food_ratio=old_ratio,
                    new_food_ratio=new_ratio,
                )
            )
    if not steps or steps[-1].day_index != days:
        steps.append(
            schemas.FoodTransitionStepCreate(
                day_index=days,
                old_food_ratio=0,
                new_food_ratio=100,
            )
        )
    return steps


def resolve_synced_plan_id_for_cat(db: Session, target_cat_id: int, source_plan_id: Optional[int]) -> Optional[int]:
    """同步喂食记录时，把源猫的喂养方案映射到目标猫同组方案。"""
    if not source_plan_id:
        return None

    plan = db.query(models.FeedingPlan).filter(models.FeedingPlan.id == source_plan_id).first()
    if not plan:
        return None
    if plan.cat_id == target_cat_id:
        return plan.id
    if not plan.sync_group_id:
        return None

    sibling_plan = (
        db.query(models.FeedingPlan)
        .filter(
            models.FeedingPlan.cat_id == target_cat_id,
            models.FeedingPlan.sync_group_id == plan.sync_group_id,
        )
        .order_by(models.FeedingPlan.updated_at.desc(), models.FeedingPlan.id.desc())
        .first()
    )
    return sibling_plan.id if sibling_plan else None


def resolve_synced_transition_id_for_cat(db: Session, target_cat_id: int, source_transition_id: Optional[int]) -> Optional[int]:
    """同步喂食记录时，把源猫的换粮计划映射到目标猫同组计划。"""
    if not source_transition_id:
        return None

    transition = db.query(models.FoodTransitionPlan).filter(models.FoodTransitionPlan.id == source_transition_id).first()
    if not transition:
        return None
    if transition.cat_id == target_cat_id:
        return transition.id
    if not transition.sync_group_id:
        return None

    sibling_transition = (
        db.query(models.FoodTransitionPlan)
        .filter(
            models.FoodTransitionPlan.cat_id == target_cat_id,
            models.FoodTransitionPlan.sync_group_id == transition.sync_group_id,
        )
        .order_by(models.FoodTransitionPlan.updated_at.desc(), models.FoodTransitionPlan.id.desc())
        .first()
    )
    return sibling_transition.id if sibling_transition else None


def build_record_payload_for_cat(db: Session, target_cat_id: int, payload_data: dict[str, Any]) -> dict[str, Any]:
    """构造目标猫的喂食记录 payload，防止跨猫复用外键。"""
    normalized_payload = dict(payload_data)
    normalized_payload["plan_id"] = resolve_synced_plan_id_for_cat(db, target_cat_id, normalized_payload.get("plan_id"))
    normalized_payload["transition_plan_id"] = resolve_synced_transition_id_for_cat(
        db,
        target_cat_id,
        normalized_payload.get("transition_plan_id"),
    )
    return normalized_payload


def serialize_overview(cat_id: int, db: Session) -> schemas.FeedingOverview:
    today_start = datetime.combine(datetime.now().date(), time.min)
    today_end = datetime.combine(datetime.now().date(), time.max)

    active_plan = (
        db.query(models.FeedingPlan)
        .filter(models.FeedingPlan.cat_id == cat_id, models.FeedingPlan.is_active.is_(True))
        .order_by(models.FeedingPlan.updated_at.desc())
        .first()
    )
    active_transition = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(
            models.FoodTransitionPlan.cat_id == cat_id,
            models.FoodTransitionPlan.status.in_(["planned", "in_progress"]),
        )
        .order_by(models.FoodTransitionPlan.start_date.desc(), models.FoodTransitionPlan.updated_at.desc())
        .first()
    )
    active_courses = (
        db.query(models.SupplementCourse)
        .filter(models.SupplementCourse.cat_id == cat_id, models.SupplementCourse.is_active.is_(True))
        .order_by(models.SupplementCourse.updated_at.desc())
        .all()
    )
    today_records = (
        db.query(models.FeedingRecord)
        .filter(
            models.FeedingRecord.cat_id == cat_id,
            models.FeedingRecord.recorded_at >= today_start,
            models.FeedingRecord.recorded_at <= today_end,
        )
        .order_by(models.FeedingRecord.recorded_at.desc())
        .all()
    )
    recent_reactions = (
        db.query(models.FeedingRecord)
        .filter(
            models.FeedingRecord.cat_id == cat_id,
            models.FeedingRecord.reaction.isnot(None),
            models.FeedingRecord.reaction != "none",
        )
        .order_by(models.FeedingRecord.recorded_at.desc())
        .limit(5)
        .all()
    )

    summary = {
        "main_food_count": sum(1 for record in today_records if record.record_type == "main_food"),
        "canned_food_count": sum(1 for record in today_records if record.record_type == "canned_food"),
        "treat_count": sum(1 for record in today_records if record.record_type == "treat"),
        "supplement_count": sum(1 for record in today_records if record.record_type == "supplement"),
        "refused_count": sum(1 for record in today_records if record.consumed_status in {"refused", "half"}),
    }

    return schemas.FeedingOverview(
        active_plan=annotate_sync_group_size(db, active_plan, models.FeedingPlan),
        active_transition_plan=annotate_sync_group_size(db, active_transition, models.FoodTransitionPlan),
        active_supplement_courses=annotate_sync_group_size(db, active_courses, models.SupplementCourse),
        today_records=annotate_sync_group_size(db, today_records, models.FeedingRecord),
        recent_reactions=annotate_sync_group_size(db, recent_reactions, models.FeedingRecord),
        daily_summary=summary,
    )


@router.get("/cats/{cat_id}/feeding/overview", response_model=schemas.FeedingOverview)
def get_feeding_overview(cat_id: int, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    return serialize_overview(cat_id, db)


@router.get("/cats/{cat_id}/feeding/plans", response_model=List[schemas.FeedingPlan])
def get_feeding_plans(cat_id: int, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    records = (
        db.query(models.FeedingPlan)
        .filter(models.FeedingPlan.cat_id == cat_id)
        .order_by(models.FeedingPlan.is_active.desc(), models.FeedingPlan.start_date.desc(), models.FeedingPlan.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FeedingPlan)


@router.get("/feeding/plans/group/{group_id}", response_model=List[schemas.FeedingPlan])
def get_feeding_plans_by_group(group_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(models.FeedingPlan)
        .filter(models.FeedingPlan.sync_group_id == group_id)
        .order_by(models.FeedingPlan.start_date.desc(), models.FeedingPlan.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FeedingPlan)


@router.post("/cats/{cat_id}/feeding/plans", response_model=schemas.FeedingPlan)
def create_feeding_plan(cat_id: int, payload: schemas.FeedingPlanCreate, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    if payload.is_active:
        db.query(models.FeedingPlan).filter(models.FeedingPlan.cat_id == cat_id).update({"is_active": False})
    plan = models.FeedingPlan(cat_id=cat_id, **payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return annotate_sync_group_size(db, plan, models.FeedingPlan)


@router.post("/cats/{cat_id}/feeding/plans/batch", response_model=List[schemas.FeedingPlan])
def create_feeding_plan_batch(cat_id: int, payload: schemas.FeedingPlanBatchCreateRequest, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    valid_cat_ids = validate_cat_ids(payload.cat_ids, db)

    created: List[models.FeedingPlan] = []
    plan_data = payload.plan.model_dump()
    for target_cat_id in valid_cat_ids:
        if plan_data.get("is_active"):
            db.query(models.FeedingPlan).filter(models.FeedingPlan.cat_id == target_cat_id).update({"is_active": False})
        new_plan = models.FeedingPlan(cat_id=target_cat_id, **plan_data)
        db.add(new_plan)
        created.append(new_plan)

    db.commit()
    for record in created:
        db.refresh(record)
    return annotate_sync_group_size(db, created, models.FeedingPlan)


@router.put("/feeding/plans/{plan_id}", response_model=schemas.FeedingPlan)
def update_feeding_plan(plan_id: int, payload: schemas.FeedingPlanUpdate, db: Session = Depends(get_db)):
    plan = db.query(models.FeedingPlan).filter(models.FeedingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="喂养方案不存在")

    update_data = payload.model_dump(exclude_unset=True)
    if update_data.get("is_active"):
        db.query(models.FeedingPlan).filter(
            models.FeedingPlan.cat_id == plan.cat_id,
            models.FeedingPlan.id != plan_id,
        ).update({"is_active": False})
    for key, value in update_data.items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return annotate_sync_group_size(db, plan, models.FeedingPlan)


@router.delete("/feeding/plans/{plan_id}")
def delete_feeding_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.query(models.FeedingPlan).filter(models.FeedingPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="喂养方案不存在")
    db.delete(plan)
    db.commit()
    return {"message": "删除成功"}


@router.get("/cats/{cat_id}/feeding/records", response_model=List[schemas.FeedingRecord])
def get_feeding_records(cat_id: int, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    records = (
        db.query(models.FeedingRecord)
        .filter(models.FeedingRecord.cat_id == cat_id)
        .order_by(models.FeedingRecord.recorded_at.desc(), models.FeedingRecord.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FeedingRecord)


@router.get("/feeding/records/group/{group_id}", response_model=List[schemas.FeedingRecord])
def get_feeding_records_by_group(group_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(models.FeedingRecord)
        .filter(models.FeedingRecord.sync_group_id == group_id)
        .order_by(models.FeedingRecord.recorded_at.desc(), models.FeedingRecord.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FeedingRecord)


@router.post("/cats/{cat_id}/feeding/records", response_model=schemas.FeedingRecord)
def create_feeding_record(cat_id: int, payload: schemas.FeedingRecordCreate, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    payload_data = build_record_payload_for_cat(db, cat_id, payload.model_dump())
    record = models.FeedingRecord(cat_id=cat_id, **payload_data)
    db.add(record)
    db.commit()
    db.refresh(record)
    return annotate_sync_group_size(db, record, models.FeedingRecord)


@router.post("/cats/{cat_id}/feeding/records/batch", response_model=List[schemas.FeedingRecord])
def create_feeding_record_batch(cat_id: int, payload: schemas.FeedingRecordBatchCreateRequest, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    valid_cat_ids = validate_cat_ids(payload.cat_ids, db)

    created: List[models.FeedingRecord] = []
    record_data = payload.record.model_dump()
    for target_cat_id in valid_cat_ids:
        target_payload = build_record_payload_for_cat(db, target_cat_id, record_data)
        new_record = models.FeedingRecord(cat_id=target_cat_id, **target_payload)
        db.add(new_record)
        created.append(new_record)

    db.commit()
    for record in created:
        db.refresh(record)
    return annotate_sync_group_size(db, created, models.FeedingRecord)


@router.put("/feeding/records/{record_id}", response_model=schemas.FeedingRecord)
def update_feeding_record(record_id: int, payload: schemas.FeedingRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(models.FeedingRecord).filter(models.FeedingRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="喂食记录不存在")

    update_data = payload.model_dump(exclude_unset=True)
    update_data = build_record_payload_for_cat(db, record.cat_id, update_data)
    for key, value in update_data.items():
        setattr(record, key, value)
    db.commit()
    db.refresh(record)
    return annotate_sync_group_size(db, record, models.FeedingRecord)


@router.delete("/feeding/records/{record_id}")
def delete_feeding_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.FeedingRecord).filter(models.FeedingRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="喂食记录不存在")
    db.delete(record)
    db.commit()
    return {"message": "删除成功"}


@router.get("/cats/{cat_id}/feeding/transitions", response_model=List[schemas.FoodTransitionPlan])
def get_transition_plans(cat_id: int, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    records = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(models.FoodTransitionPlan.cat_id == cat_id)
        .order_by(models.FoodTransitionPlan.start_date.desc(), models.FoodTransitionPlan.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FoodTransitionPlan)


@router.get("/feeding/transitions/group/{group_id}", response_model=List[schemas.FoodTransitionPlan])
def get_transition_plans_by_group(group_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(models.FoodTransitionPlan.sync_group_id == group_id)
        .order_by(models.FoodTransitionPlan.start_date.desc(), models.FoodTransitionPlan.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.FoodTransitionPlan)


@router.post("/cats/{cat_id}/feeding/transitions", response_model=schemas.FoodTransitionPlan)
def create_transition_plan(cat_id: int, payload: schemas.FoodTransitionPlanCreate, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    data = payload.model_dump(exclude={"steps"})
    transition = models.FoodTransitionPlan(cat_id=cat_id, **data)
    db.add(transition)
    db.flush()

    steps = payload.steps or get_transition_templates(payload.planned_days)
    for step in steps:
        db.add(models.FoodTransitionStep(transition_plan_id=transition.id, **step.model_dump()))

    db.commit()
    transition = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(models.FoodTransitionPlan.id == transition.id)
        .first()
    )
    return annotate_sync_group_size(db, transition, models.FoodTransitionPlan)


@router.post("/cats/{cat_id}/feeding/transitions/batch", response_model=List[schemas.FoodTransitionPlan])
def create_transition_plan_batch(cat_id: int, payload: schemas.FoodTransitionPlanBatchCreateRequest, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    valid_cat_ids = validate_cat_ids(payload.cat_ids, db)

    created_ids: List[int] = []
    data = payload.transition.model_dump(exclude={"steps"})
    steps = payload.transition.steps or get_transition_templates(payload.transition.planned_days)

    for target_cat_id in valid_cat_ids:
        transition = models.FoodTransitionPlan(cat_id=target_cat_id, **data)
        db.add(transition)
        db.flush()
        for step in steps:
            db.add(models.FoodTransitionStep(transition_plan_id=transition.id, **step.model_dump()))
        created_ids.append(transition.id)

    db.commit()
    created = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(models.FoodTransitionPlan.id.in_(created_ids))
        .order_by(models.FoodTransitionPlan.start_date.desc(), models.FoodTransitionPlan.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, created, models.FoodTransitionPlan)


@router.put("/feeding/transitions/{transition_id}", response_model=schemas.FoodTransitionPlan)
def update_transition_plan(transition_id: int, payload: schemas.FoodTransitionPlanUpdate, db: Session = Depends(get_db)):
    transition = (
        db.query(models.FoodTransitionPlan)
        .options(selectinload(models.FoodTransitionPlan.steps))
        .filter(models.FoodTransitionPlan.id == transition_id)
        .first()
    )
    if not transition:
        raise HTTPException(status_code=404, detail="换粮计划不存在")

    update_data = payload.model_dump(exclude_unset=True, exclude={"steps"})
    for key, value in update_data.items():
        setattr(transition, key, value)

    if payload.steps is not None:
        transition.steps.clear()
        db.flush()
        for step in payload.steps:
            transition.steps.append(models.FoodTransitionStep(**step.model_dump()))

    db.commit()
    db.refresh(transition)
    return annotate_sync_group_size(db, transition, models.FoodTransitionPlan)


@router.delete("/feeding/transitions/{transition_id}")
def delete_transition_plan(transition_id: int, db: Session = Depends(get_db)):
    transition = db.query(models.FoodTransitionPlan).filter(models.FoodTransitionPlan.id == transition_id).first()
    if not transition:
        raise HTTPException(status_code=404, detail="换粮计划不存在")
    db.delete(transition)
    db.commit()
    return {"message": "删除成功"}


@router.get("/cats/{cat_id}/feeding/supplements", response_model=List[schemas.SupplementCourse])
def get_supplement_courses(cat_id: int, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    records = (
        db.query(models.SupplementCourse)
        .filter(models.SupplementCourse.cat_id == cat_id)
        .order_by(models.SupplementCourse.is_active.desc(), models.SupplementCourse.start_date.desc(), models.SupplementCourse.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.SupplementCourse)


@router.get("/feeding/supplements/group/{group_id}", response_model=List[schemas.SupplementCourse])
def get_supplement_courses_by_group(group_id: str, db: Session = Depends(get_db)):
    records = (
        db.query(models.SupplementCourse)
        .filter(models.SupplementCourse.sync_group_id == group_id)
        .order_by(models.SupplementCourse.start_date.desc(), models.SupplementCourse.id.desc())
        .all()
    )
    return annotate_sync_group_size(db, records, models.SupplementCourse)


@router.post("/cats/{cat_id}/feeding/supplements", response_model=schemas.SupplementCourse)
def create_supplement_course(cat_id: int, payload: schemas.SupplementCourseCreate, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    course = models.SupplementCourse(cat_id=cat_id, **payload.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return annotate_sync_group_size(db, course, models.SupplementCourse)


@router.post("/cats/{cat_id}/feeding/supplements/batch", response_model=List[schemas.SupplementCourse])
def create_supplement_course_batch(cat_id: int, payload: schemas.SupplementCourseBatchCreateRequest, db: Session = Depends(get_db)):
    ensure_cat_exists(cat_id, db)
    valid_cat_ids = validate_cat_ids(payload.cat_ids, db)

    created: List[models.SupplementCourse] = []
    course_data = payload.course.model_dump()
    for target_cat_id in valid_cat_ids:
        new_course = models.SupplementCourse(cat_id=target_cat_id, **course_data)
        db.add(new_course)
        created.append(new_course)

    db.commit()
    for record in created:
        db.refresh(record)
    return annotate_sync_group_size(db, created, models.SupplementCourse)


@router.put("/feeding/supplements/{course_id}", response_model=schemas.SupplementCourse)
def update_supplement_course(course_id: int, payload: schemas.SupplementCourseUpdate, db: Session = Depends(get_db)):
    course = db.query(models.SupplementCourse).filter(models.SupplementCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="补剂疗程不存在")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return annotate_sync_group_size(db, course, models.SupplementCourse)


@router.delete("/feeding/supplements/{course_id}")
def delete_supplement_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(models.SupplementCourse).filter(models.SupplementCourse.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="补剂疗程不存在")
    db.delete(course)
    db.commit()
    return {"message": "删除成功"}
