"""
猫咪批量操作和搜索功能 - 高级测试套件

测试内容：
1. 边界条件测试
2. 异常场景测试
3. 并发安全测试
4. 性能测试
5. 数据一致性测试
6. Unicode 支持
7. SQL 注入防御

创建时间：2026-05-25 16:00
创建者：虾虾 🦐（代 Codex 执行）
"""
import os
import sys
from pathlib import Path
from datetime import date
from concurrent.futures import ThreadPoolExecutor
import time

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

# 使用文件型 SQLite，避免并发 TestClient 请求共用同一 in-memory 连接。
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_cats_advanced.db"
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


@pytest.fixture(scope="function")
def setup_test_env():
    """每个测试函数独立的测试环境"""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(setup_test_env):
    """创建测试客户端"""
    return TestClient(app)


@pytest.fixture()
def db_session(setup_test_env):
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


# ==================== 边界条件测试 ====================

class TestBoundaryConditions:
    """边界条件测试"""

    def test_batch_delete_single_cat(self, client, test_user, db_session):
        """测试批量删除单只猫咪（边界值）"""
        cat = models.Cat(
            name="单猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)

        response = client.post(
            f"/api/cats/batch-delete?cat_ids={cat.id}&user_id={test_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 1

    def test_batch_delete_max_limit(self, client, test_user, db_session):
        """测试批量删除最大限制（50只）"""
        # 创建50只猫咪
        cat_ids = []
        for i in range(50):
            cat = models.Cat(
                name=f"猫{i}",
                gender="male",
                breed="测试",
                birth_date=date(2023, 1, 1),
                owner_id=test_user.id
            )
            db_session.add(cat)
            db_session.commit()
            db_session.refresh(cat)
            cat_ids.append(cat.id)

        # 批量删除50只
        url = f"/api/cats/batch-delete?user_id={test_user.id}"
        for cat_id in cat_ids:
            url += f"&cat_ids={cat_id}"

        response = client.post(url)
        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 50

    def test_search_empty_keyword(self, client, test_user, db_session):
        """测试空关键词搜索"""
        # 创建一只猫
        cat = models.Cat(
            name="测试猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 空关键词应该返回所有猫咪
        response = client.get(f"/api/cats/search?user_id={test_user.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_search_special_characters(self, client, test_user, db_session):
        """测试特殊字符搜索"""
        cat = models.Cat(
            name="测试%猫",
            gender="male",
            breed="测试_品种",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 搜索包含特殊字符的关键词
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=%")

        assert response.status_code == 200
        # 应该正确处理特殊字符，不应该报错

    def test_search_case_insensitive(self, client, test_user, db_session):
        """测试大小写不敏感搜索"""
        cat = models.Cat(
            name="XIAOMAO",
            gender="male",
            breed="TEST",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 用小写搜索大写
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=xiaomao")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


# ==================== 异常场景测试 ====================

class TestExceptionScenarios:
    """异常场景测试"""

    def test_batch_delete_duplicate_ids(self, client, test_user, db_session):
        """测试批量删除重复ID"""
        cat = models.Cat(
            name="重复猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)

        # 传入重复的ID
        response = client.post(
            f"/api/cats/batch-delete?cat_ids={cat.id}&cat_ids={cat.id}&user_id={test_user.id}"
        )

        assert response.status_code == 200
        # 应该只删除一次
        data = response.json()
        assert data["success_count"] == 1

    def test_batch_delete_negative_id(self, client, test_user):
        """测试批量删除负数ID"""
        response = client.post(
            f"/api/cats/batch-delete?cat_ids=-1&user_id={test_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["failed_count"] == 1

    def test_batch_delete_zero_id(self, client, test_user):
        """测试批量删除零ID"""
        response = client.post(
            f"/api/cats/batch-delete?cat_ids=0&user_id={test_user.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["failed_count"] == 1

    def test_search_invalid_gender(self, client, test_user, db_session):
        """测试无效性别参数"""
        cat = models.Cat(
            name="测试猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 传入无效的性别值
        response = client.get(f"/api/cats/search?user_id={test_user.id}&gender=invalid")

        assert response.status_code == 200
        data = response.json()
        # 应该返回空结果（没有匹配的）
        assert len(data) == 0

    def test_search_nonexistent_user(self, client):
        """测试搜索不存在的用户"""
        response = client.get("/api/cats/search?user_id=99999")

        assert response.status_code == 200
        data = response.json()
        # 应该返回空结果
        assert len(data) == 0


# ==================== 数据一致性测试 ====================

class TestDataConsistency:
    """数据一致性测试"""

    def test_batch_delete_cascade(self, client, test_user, db_session):
        """测试批量删除级联效果"""
        # 创建猫咪和相关数据
        cat = models.Cat(
            name="级联猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()
        db_session.refresh(cat)

        # 添加体重记录
        weight = models.WeightRecord(
            cat_id=cat.id,
            date=date(2023, 1, 1),
            weight=5000.0
        )
        db_session.add(weight)
        db_session.commit()

        # 批量删除猫咪
        response = client.post(
            f"/api/cats/batch-delete?cat_ids={cat.id}&user_id={test_user.id}"
        )

        assert response.status_code == 200

        # 验证体重记录也被删除（级联删除）
        remaining_weights = db_session.query(models.WeightRecord).filter(
            models.WeightRecord.cat_id == cat.id
        ).all()
        assert len(remaining_weights) == 0

    def test_search_result_consistency(self, client, test_user, db_session):
        """测试搜索结果一致性"""
        # 创建猫咪
        cat = models.Cat(
            name="一致性猫",
            gender="male",
            breed="测试品种",
            color="测试颜色",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 多次搜索应该返回相同结果
        response1 = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=一致性")
        response2 = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=一致性")

        assert response1.json() == response2.json()


# ==================== Unicode 支持 ====================

class TestUnicodeSupport:
    """Unicode 支持测试"""

    def test_chinese_name(self, client, test_user, db_session):
        """测试中文名字搜索"""
        cat = models.Cat(
            name="花卷小猫咪",
            gender="male",
            breed="中华田园猫",
            color="橘白相间",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=花卷")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "花卷小猫咪"

    def test_emoji_in_name(self, client, test_user, db_session):
        """测试Emoji名字"""
        cat = models.Cat(
            name="小橘🐱",
            gender="male",
            breed="橘猫",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=🐱")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1

    def test_japanese_characters(self, client, test_user, db_session):
        """测试日文字符"""
        cat = models.Cat(
            name="ネコ",
            gender="male",
            breed="日本猫",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=ネコ")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1


# ==================== SQL 注入防御 ====================

class TestSQLInjectionDefense:
    """SQL 注入防御测试"""

    def test_injection_in_keyword(self, client, test_user, db_session):
        """测试关键词中的SQL注入"""
        cat = models.Cat(
            name="正常猫",
            gender="male",
            breed="测试",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        # 尝试SQL注入
        injection_attempts = [
            "'; DROP TABLE cats; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM cats WHERE 1=1",
        ]

        for injection in injection_attempts:
            response = client.get(
                f"/api/cats/search?user_id={test_user.id}&keyword={injection}"
            )

            assert response.status_code == 200
            # 应该返回空结果，而不是执行注入
            data = response.json()
            assert isinstance(data, list)

            # 验证猫咪没有被删除
            remaining = db_session.query(models.Cat).filter(
                models.Cat.owner_id == test_user.id
            ).all()
            assert len(remaining) == 1

    def test_injection_in_breed_filter(self, client, test_user, db_session):
        """测试品种筛选中的SQL注入"""
        cat = models.Cat(
            name="测试猫",
            gender="male",
            breed="正常品种",
            birth_date=date(2023, 1, 1),
            owner_id=test_user.id
        )
        db_session.add(cat)
        db_session.commit()

        response = client.get(
            f"/api/cats/search?user_id={test_user.id}&breed='; DROP TABLE cats; --"
        )

        assert response.status_code == 200
        # 应该返回空结果，而不是执行注入
        data = response.json()
        assert isinstance(data, list)


# ==================== 性能测试 ====================

class TestPerformance:
    """性能测试"""

    def test_search_large_dataset(self, client, test_user, db_session):
        """测试大数据集搜索性能"""
        # 创建100只猫咪
        for i in range(100):
            cat = models.Cat(
                name=f"猫{i}",
                gender="male" if i % 2 == 0 else "female",
                breed=f"品种{i % 10}",
                birth_date=date(2023, 1, 1),
                owner_id=test_user.id
            )
            db_session.add(cat)
        db_session.commit()

        # 测量搜索时间
        start_time = time.time()
        response = client.get(f"/api/cats/search?user_id={test_user.id}&keyword=猫")
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 100

        # 性能要求：100条数据搜索时间 < 1秒
        assert elapsed < 1.0, f"搜索耗时 {elapsed:.2f}s，超过1秒阈值"

    def test_batch_delete_performance(self, client, test_user, db_session):
        """测试批量删除性能"""
        # 创建50只猫咪
        cat_ids = []
        for i in range(50):
            cat = models.Cat(
                name=f"性能猫{i}",
                gender="male",
                breed="测试",
                birth_date=date(2023, 1, 1),
                owner_id=test_user.id
            )
            db_session.add(cat)
            db_session.commit()
            db_session.refresh(cat)
            cat_ids.append(cat.id)

        # 测量删除时间
        start_time = time.time()
        url = f"/api/cats/batch-delete?user_id={test_user.id}"
        for cat_id in cat_ids:
            url += f"&cat_ids={cat_id}"

        response = client.post(url)
        elapsed = time.time() - start_time

        assert response.status_code == 200
        data = response.json()
        assert data["success_count"] == 50

        # 性能要求：50条删除时间 < 2秒
        assert elapsed < 2.0, f"删除耗时 {elapsed:.2f}s，超过2秒阈值"


# ==================== 并发安全测试 ====================

class TestConcurrencySafety:
    """并发安全测试"""

    def test_concurrent_search(self, client, test_user, db_session):
        """测试并发搜索"""
        user_id = test_user.id
        # 创建测试数据
        for i in range(10):
            cat = models.Cat(
                name=f"并发猫{i}",
                gender="male",
                breed="测试",
                birth_date=date(2023, 1, 1),
                owner_id=user_id
            )
            db_session.add(cat)
        db_session.commit()

        # 并发搜索
        def search_task():
            response = client.get(f"/api/cats/search?user_id={user_id}&keyword=并发")
            return response.status_code == 200

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(search_task) for _ in range(10)]
            results = [f.result() for f in futures]

        # 所有请求都应该成功
        assert all(results)

    def test_concurrent_batch_delete_different_cats(self, client, test_user, db_session):
        """测试并发删除不同猫咪"""
        user_id = test_user.id
        # 创建多只猫咪
        cat_ids = []
        for i in range(10):
            cat = models.Cat(
                name=f"删除猫{i}",
                gender="male",
                breed="测试",
                birth_date=date(2023, 1, 1),
                owner_id=user_id
            )
            db_session.add(cat)
            db_session.commit()
            db_session.refresh(cat)
            cat_ids.append(cat.id)

        # 并发删除不同的猫咪
        def delete_task(cat_id):
            response = client.post(
                f"/api/cats/batch-delete?cat_ids={cat_id}&user_id={user_id}"
            )
            return response.status_code == 200

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(delete_task, cat_id) for cat_id in cat_ids]
            results = [f.result() for f in futures]

        # 所有删除都应该成功
        assert all(results)


# ==================== 运行测试 ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
