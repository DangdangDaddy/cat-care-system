from datetime import date
from sqlalchemy.orm import Session
from database import SessionLocal
import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def init_data():
    db: Session = SessionLocal()
    try:
        # 检查是否已有数据
        if db.query(models.User).first():
            return
        
        # 创建测试用户
        hashed_password = pwd_context.hash("123456")
        test_user = models.User(username="demo", hashed_password=hashed_password)
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        
        # 创建测试猫咪
        cat1 = models.Cat(
            name="咪咪",
            gender="female",
            breed="英短蓝猫",
            birth_date=date(2023, 3, 15),
            neutered=True,
            owner_id=test_user.id
        )
        cat2 = models.Cat(
            name="小橘",
            gender="male",
            breed="橘猫",
            birth_date=date(2023, 6, 20),
            neutered=False,
            owner_id=test_user.id
        )
        db.add(cat1)
        db.add(cat2)
        db.commit()
        db.refresh(cat1)
        db.refresh(cat2)
        
        # 添加体重记录
        weight_data_1 = [
            (date(2023, 4, 15), 850),
            (date(2023, 5, 15), 1200),
            (date(2023, 6, 15), 1800),
            (date(2023, 7, 15), 2500),
            (date(2023, 8, 15), 3200),
            (date(2023, 9, 15), 3800),
            (date(2023, 10, 15), 4200),
            (date(2023, 11, 15), 4500),
            (date(2023, 12, 15), 4700),
            (date(2024, 1, 15), 4800),
        ]
        
        weight_data_2 = [
            (date(2023, 7, 20), 750),
            (date(2023, 8, 20), 1100),
            (date(2023, 9, 20), 1600),
            (date(2023, 10, 20), 2200),
            (date(2023, 11, 20), 2800),
            (date(2023, 12, 20), 3300),
            (date(2024, 1, 20), 3700),
            (date(2024, 2, 20), 4000),
        ]
        
        for w_date, w_weight in weight_data_1:
            db.add(models.WeightRecord(cat_id=cat1.id, date=w_date, weight=w_weight))
        
        for w_date, w_weight in weight_data_2:
            db.add(models.WeightRecord(cat_id=cat2.id, date=w_date, weight=w_weight))
        
        db.commit()
        print("初始数据已导入！测试账号: demo / 123456")
    except Exception as e:
        print(f"初始化数据失败: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_data()
