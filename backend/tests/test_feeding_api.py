from datetime import date, datetime

import models
from routers.feeding import get_transition_templates


def seed_cat(db_session) -> int:
    user = models.User(username=f"tester-{datetime.utcnow().timestamp()}", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    cat = models.Cat(
        name="测试猫",
        gender="female",
        breed="中华田园猫",
        birth_date=date(2024, 1, 1),
        neutered=True,
        owner_id=user.id,
    )
    db_session.add(cat)
    db_session.commit()
    db_session.refresh(cat)
    return cat.id


def seed_cats(db_session, count: int = 2) -> list[int]:
    user = models.User(username=f"tester-{datetime.utcnow().timestamp()}", hashed_password="x")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    cat_ids: list[int] = []
    for index in range(count):
        cat = models.Cat(
            name=f"测试猫{index + 1}",
            gender="female",
            breed="中华田园猫",
            birth_date=date(2024, 1, 1),
            neutered=True,
            owner_id=user.id,
        )
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)
        cat_ids.append(cat.id)
    return cat_ids


def test_transition_template_defaults():
    steps = get_transition_templates(7)
    assert steps[0].old_food_ratio == 75
    assert steps[-1].new_food_ratio == 100
    assert steps[-1].day_index == 7


def test_create_plan_record_transition_and_overview(client, db_session):
    cat_id = seed_cat(db_session)

    plan_response = client.post(
        f"/api/cats/{cat_id}/feeding/plans",
        json={
            "name": "5月主粮方案",
            "start_date": "2026-05-14",
            "food_type": "mixed",
            "brand": "渴望",
            "product_name": "鸡肉配方",
            "life_stage": "adult",
            "complete_balance_status": "yes",
            "daily_amount": 65,
            "amount_unit": "g",
            "feeding_frequency": "每日2次",
            "daily_calories": 240,
            "hydration_strategy": "拌水",
            "notes": "肠胃敏感期",
            "is_active": True,
        },
    )
    assert plan_response.status_code == 200
    plan_payload = plan_response.json()
    assert plan_payload["is_active"] is True

    transition_response = client.post(
        f"/api/cats/{cat_id}/feeding/transitions",
        json={
            "name": "A粮换B粮",
            "start_date": "2026-05-14",
            "planned_days": 7,
            "old_food_name": "A粮",
            "new_food_name": "B粮",
            "reason": "换品牌",
            "status": "in_progress",
            "observation_notes": "持续观察便便",
            "steps": [],
        },
    )
    assert transition_response.status_code == 200
    transition_payload = transition_response.json()
    assert len(transition_payload["steps"]) >= 4

    supplement_response = client.post(
        f"/api/cats/{cat_id}/feeding/supplements",
        json={
            "product_name": "赖氨酸",
            "category": "补剂",
            "purpose": "免疫支持",
            "start_date": "2026-05-14",
            "frequency": "每日1次",
            "dosage": 1,
            "dosage_unit": "scoop",
            "feeding_method": "拌罐头",
            "source": "医生建议",
            "response": "接受度高",
            "risk_notes": "持续观察食欲",
            "is_active": True,
        },
    )
    assert supplement_response.status_code == 200

    record_response = client.post(
        f"/api/cats/{cat_id}/feeding/records",
        json={
            "recorded_at": "2026-05-14T09:30:00",
            "record_type": "main_food",
            "brand": "渴望",
            "item_name": "鸡肉配方",
            "flavor": "鸡肉",
            "amount": 35,
            "amount_unit": "g",
            "calories": 120,
            "consumed_status": "finished",
            "feeding_method": "正常喂食",
            "notes": "早饭正常",
            "reaction": "soft_stool",
            "plan_id": plan_payload["id"],
            "transition_plan_id": transition_payload["id"],
        },
    )
    assert record_response.status_code == 200

    overview_response = client.get(f"/api/cats/{cat_id}/feeding/overview")
    assert overview_response.status_code == 200
    overview_payload = overview_response.json()
    assert overview_payload["active_plan"]["name"] == "5月主粮方案"
    assert overview_payload["active_transition_plan"]["name"] == "A粮换B粮"
    assert overview_payload["active_supplement_courses"][0]["product_name"] == "赖氨酸"
    assert overview_payload["recent_reactions"][0]["reaction"] == "soft_stool"


def test_creating_new_active_plan_deactivates_previous(client, db_session):
    cat_id = seed_cat(db_session)
    first_plan = client.post(
        f"/api/cats/{cat_id}/feeding/plans",
        json={
            "name": "旧方案",
            "start_date": "2026-05-01",
            "food_type": "dry_food",
            "brand": "A",
            "product_name": "A1",
            "complete_balance_status": "yes",
            "is_active": True,
        },
    )
    assert first_plan.status_code == 200

    second_plan = client.post(
        f"/api/cats/{cat_id}/feeding/plans",
        json={
            "name": "新方案",
            "start_date": "2026-05-14",
            "food_type": "wet_food",
            "brand": "B",
            "product_name": "B1",
            "complete_balance_status": "yes",
            "is_active": True,
        },
    )
    assert second_plan.status_code == 200

    list_response = client.get(f"/api/cats/{cat_id}/feeding/plans")
    plans = list_response.json()
    assert plans[0]["name"] == "新方案"
    assert plans[0]["is_active"] is True
    old_plan = next(item for item in plans if item["name"] == "旧方案")
    assert old_plan["is_active"] is False


def test_batch_sync_endpoints_support_plans_transitions_and_supplements(client, db_session):
    cat_ids = seed_cats(db_session, count=2)

    plan_group_id = f"plan-sync-{datetime.utcnow().timestamp()}"
    plan_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/plans/batch",
        json={
            "cat_ids": cat_ids,
            "plan": {
                "name": "共享喂养方案",
                "start_date": "2026-05-22",
                "food_type": "mixed",
                "brand": "测试品牌",
                "product_name": "共享主粮",
                "complete_balance_status": "yes",
                "sync_group_id": plan_group_id,
                "is_active": True,
            },
        },
    )
    assert plan_response.status_code == 200
    plans = plan_response.json()
    assert len(plans) == 2
    assert {item["cat_id"] for item in plans} == set(cat_ids)
    assert {item["sync_group_id"] for item in plans} == {plan_group_id}
    assert {item["sync_group_size"] for item in plans} == {2}

    group_plans_response = client.get(f"/api/feeding/plans/group/{plan_group_id}")
    assert group_plans_response.status_code == 200
    assert len(group_plans_response.json()) == 2

    detached_plan_id = next(item["id"] for item in plans if item["cat_id"] == cat_ids[1])
    detach_response = client.put(
        f"/api/feeding/plans/{detached_plan_id}",
        json={"sync_group_id": None},
    )
    assert detach_response.status_code == 200
    assert detach_response.json()["sync_group_size"] == 0

    updated_group_plans_response = client.get(f"/api/feeding/plans/group/{plan_group_id}")
    assert updated_group_plans_response.status_code == 200
    updated_group_plans = updated_group_plans_response.json()
    assert len(updated_group_plans) == 1
    assert updated_group_plans[0]["cat_id"] == cat_ids[0]

    transition_group_id = f"transition-sync-{datetime.utcnow().timestamp()}"
    transition_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/transitions/batch",
        json={
            "cat_ids": cat_ids,
            "transition": {
                "name": "共享换粮计划",
                "start_date": "2026-05-22",
                "planned_days": 7,
                "old_food_name": "旧粮",
                "new_food_name": "新粮",
                "status": "planned",
                "sync_group_id": transition_group_id,
                "steps": [],
            },
        },
    )
    assert transition_response.status_code == 200
    transitions = transition_response.json()
    assert len(transitions) == 2
    assert {item["sync_group_id"] for item in transitions} == {transition_group_id}
    assert {item["sync_group_size"] for item in transitions} == {2}
    assert all(len(item["steps"]) >= 4 for item in transitions)

    group_transitions_response = client.get(f"/api/feeding/transitions/group/{transition_group_id}")
    assert group_transitions_response.status_code == 200
    assert len(group_transitions_response.json()) == 2

    supplement_group_id = f"supplement-sync-{datetime.utcnow().timestamp()}"
    supplement_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/supplements/batch",
        json={
            "cat_ids": cat_ids,
            "course": {
                "product_name": "共享赖氨酸",
                "category": "补剂",
                "purpose": "免疫支持",
                "start_date": "2026-05-22",
                "frequency": "每日1次",
                "sync_group_id": supplement_group_id,
                "is_active": True,
            },
        },
    )
    assert supplement_response.status_code == 200
    courses = supplement_response.json()
    assert len(courses) == 2
    assert {item["sync_group_id"] for item in courses} == {supplement_group_id}
    assert {item["sync_group_size"] for item in courses} == {2}

    group_supplements_response = client.get(f"/api/feeding/supplements/group/{supplement_group_id}")
    assert group_supplements_response.status_code == 200
    assert len(group_supplements_response.json()) == 2


def test_batch_sync_feeding_records_map_related_plan_and_transition_ids(client, db_session):
    cat_ids = seed_cats(db_session, count=2)

    plan_group_id = f"plan-map-{datetime.utcnow().timestamp()}"
    plan_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/plans/batch",
        json={
            "cat_ids": cat_ids,
            "plan": {
                "name": "映射主粮方案",
                "start_date": "2026-05-22",
                "food_type": "dry_food",
                "brand": "映射品牌",
                "product_name": "映射主粮",
                "complete_balance_status": "yes",
                "sync_group_id": plan_group_id,
                "is_active": True,
            },
        },
    )
    assert plan_response.status_code == 200
    plans_by_cat = {item["cat_id"]: item for item in plan_response.json()}

    transition_group_id = f"transition-map-{datetime.utcnow().timestamp()}"
    transition_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/transitions/batch",
        json={
            "cat_ids": cat_ids,
            "transition": {
                "name": "映射换粮计划",
                "start_date": "2026-05-22",
                "planned_days": 7,
                "old_food_name": "旧粮",
                "new_food_name": "新粮",
                "status": "in_progress",
                "sync_group_id": transition_group_id,
                "steps": [],
            },
        },
    )
    assert transition_response.status_code == 200
    transitions_by_cat = {item["cat_id"]: item for item in transition_response.json()}

    record_group_id = f"record-sync-{datetime.utcnow().timestamp()}"
    record_response = client.post(
        f"/api/cats/{cat_ids[0]}/feeding/records/batch",
        json={
            "cat_ids": cat_ids,
            "record": {
                "recorded_at": "2026-05-22T08:00:00",
                "record_type": "main_food",
                "brand": "映射品牌",
                "item_name": "映射主粮",
                "amount": 30,
                "amount_unit": "g",
                "consumed_status": "finished",
                "reaction": "none",
                "plan_id": plans_by_cat[cat_ids[0]]["id"],
                "transition_plan_id": transitions_by_cat[cat_ids[0]]["id"],
                "sync_group_id": record_group_id,
            },
        },
    )
    assert record_response.status_code == 200
    records = record_response.json()
    assert len(records) == 2
    assert {item["sync_group_id"] for item in records} == {record_group_id}
    assert {item["sync_group_size"] for item in records} == {2}

    records_by_cat = {item["cat_id"]: item for item in records}
    assert records_by_cat[cat_ids[0]]["plan_id"] == plans_by_cat[cat_ids[0]]["id"]
    assert records_by_cat[cat_ids[1]]["plan_id"] == plans_by_cat[cat_ids[1]]["id"]
    assert records_by_cat[cat_ids[0]]["transition_plan_id"] == transitions_by_cat[cat_ids[0]]["id"]
    assert records_by_cat[cat_ids[1]]["transition_plan_id"] == transitions_by_cat[cat_ids[1]]["id"]

    group_records_response = client.get(f"/api/feeding/records/group/{record_group_id}")
    assert group_records_response.status_code == 200
    group_records = group_records_response.json()
    assert len(group_records) == 2
    assert {item["cat_id"] for item in group_records} == set(cat_ids)
