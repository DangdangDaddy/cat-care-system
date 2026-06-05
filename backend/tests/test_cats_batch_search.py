"""
猫咪批量操作和搜索功能测试

测试内容：
1. 批量删除猫咪功能
2. 猫咪搜索功能
"""
import os
import sys
from pathlib import Path
from datetime import date

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加 backend 目录到 Python 路径
BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.chdir(BACKEND_ROOT)

from database import get_db, Base
from routers import cats
import models

# 使用文件型 SQLite，保证 TestClient 请求线程和 seed 会话能共享数据。
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cats_batch_search.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(cats.router)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """每个测试用例使用独立表数据，避免唯一用户名和猫咪数据相互污染。"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture()
def db_session():
    """创建数据库会话"""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def test_user(db_session):
    """创建测试用户"""
    user = models.User(username="testuser", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture()
def test_cats(db_session, test_user):
    """创建测试猫咪数据"""
    cats_data = [
        {
            "name": "小橘",
            "gender": "male",
            "breed": "橘猫",
            "color": "橘色",
            "birth_date": date(2023, 1, 15),
            "neutered": True,
            "owner_id": test_user.id
        },
        {
            "name": "小黑",
            "gender": "female",
            "breed": "黑猫",
            "color": "黑色",
            "birth_date": date(2023, 3, 20),
            "neutered": False,
            "owner_id": test_user.id
        },
        {
            "name": "小白",
            "gender": "male",
            "breed": "白猫",
            "color": "白色",
            "birth_date": date(2023, 5, 10),
            "neutered": True,
            "owner_id": test_user.id
        },
        {
            "name": "小花",
            "gender": "female",
            "breed": "三花猫",
            "color": "三花",
            "birth_date": date(2023, 7, 25),
            "neutered": False,
            "owner_id": test_user.id
        },
    ]

    created_cats = []
    for cat_data in cats_data:
        cat = models.Cat(**cat_data)
        db_session.add(cat)
        created_cats.append(cat)

    db_session.commit()
    for cat in created_cats:
        db_session.refresh(cat)

    return created_cats


# ==================== 批量删除测试 ====================

class TestBatchDelete:
    """批量删除功能测试"""

    def test_batch_delete_success(self, client, test_user, test_cats, db_session):
        """测试批量删除成功"""
        # 选择删除前两只猫
        cat_ids = [test_cats[0].id, test_cats[1].id]

        response = client.post(
            f"/api/cats/batch-delete?cat_ids={cat_ids[0]}&cat_ids={cat_ids[1]}&user_id={test_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["success_count"] == 2
        assert data["failed_count"] == 0
        assert len(data["success_ids"]) == 2

        # 验证数据库中的猫咪数量
        remaining = db_session.query(models.Cat).filter(models.Cat.owner_id == test_user.id).all()
        assert len(remaining) == 2

    def test_batch_delete_partial_success(self, client, test_user, test_cats, db_session):
        """测试部分删除成功（包含不存在的ID）"""
        # 选择一个存在的ID和一个不存在的ID
        existing_id = test_cats[0].id
        non_existing_id = 99999

        response = client.post(
            f"/api/cats/batch-delete?cat_ids={existing_id}&cat_ids={non_existing_id}&user_id={test_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1
        assert data["failed_count"] == 1
        assert existing_id in data["success_ids"]

    def test_batch_delete_no_permission(self, client, test_user, test_cats, db_session):
        """测试删除其他用户的猫咪（无权限）"""
        # 创建另一个用户
        other_user = models.User(username="otheruser", hashed_password="hashed")
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        # 尝试用另一个用户的ID删除猫咪
        cat_id = test_cats[0].id

        response = client.post(
            f"/api/cats/batch-delete?cat_ids={cat_id}&user_id={other_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 0
        assert data["failed_count"] == 1

    def test_batch_delete_empty_list(self, client, test_user):
        """测试空ID列表"""
        response = client.post(f"/api/cats/batch-delete?user_id={test_user.id}")
        assert response.status_code == 400

    def test_batch_delete_too_many(self, client, test_user):
        """测试超过限制的批量删除"""
        # 创建51个ID
        cat_ids = list(range(1, 52))
        url = f"/api/cats/batch-delete?user_id={test_user.id}"
        for cat_id in cat_ids:
            url += f"&cat_ids={cat_id}"

        response = client.post(url)
        assert response.status_code == 400


# ==================== 搜索功能测试 ====================

class TestSearchCats:
    """搜索功能测试"""

    def test_search_by_keyword_name(self, client, test_user, test_cats):
        """测试按名字搜索"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=小橘")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "小橘"

    def test_search_by_keyword_breed(self, client, test_user, test_cats):
        """测试按品种搜索"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=橘猫")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "小橘"

    def test_search_by_keyword_color(self, client, test_user, test_cats):
        """测试按毛色搜索"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=黑色")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "小黑"

    def test_search_by_gender(self, client, test_user, test_cats):
        """测试按性别筛选"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&gender=male")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 小橘和小白
        for cat in data:
            assert cat["gender"] == "male"

    def test_search_by_neutered(self, client, test_user, test_cats):
        """测试按绝育状态筛选"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&neutered=true")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 小橘和小白
        for cat in data:
            assert cat["neutered"] == True

    def test_search_combined(self, client, test_user, test_cats):
        """测试组合搜索"""
        response = client.get(
            f"/api/cats/search?user_id={test_user.id}&gender=female&neutered=false"
        )

        assert response.status_code == 200
        data = response.json()
        # 小黑和小花都是母猫且未绝育
        assert len(data) == 2

    def test_search_no_results(self, client, test_user, test_cats):
        """测试无结果的搜索"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=不存在的猫")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_user_isolation(self, client, test_user, test_cats, db_session):
        """测试用户隔离（搜索不到其他用户的猫咪）"""
        # 创建另一个用户和他的猫咪
        other_user = models.User(username="otheruser2", hashed_password="hashed")
        db_session.add(other_user)
        db_session.commit()
        db_session.refresh(other_user)

        other_cat = models.Cat(
            name="其他猫",
            gender="male",
            breed="测试品种",
            birth_date=date(2023, 1, 1),
            owner_id=other_user.id
        )
        db_session.add(other_cat)
        db_session.commit()

        # 用test_user搜索，应该找不到其他用户的猫
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=其他猫")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0

    def test_search_partial_match(self, client, test_user, test_cats):
        """测试部分匹配"""
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=小")

        assert response.status_code == 200
        data = response.json()
        # 小橘、小黑、小白、小花 都包含"小"
        assert len(data) == 4


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
