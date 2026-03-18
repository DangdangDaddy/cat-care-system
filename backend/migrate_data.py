#!/usr/bin/env python3
"""
数据迁移脚本：
1. 清除现有体重数据
2. 从 初始数据.json 导入正确的体重数据
3. 更新猫咪信息（品种等）
4. 设置头像路径
"""

import json
import shutil
from pathlib import Path
from datetime import date
from sqlalchemy.orm import Session
from database import SessionLocal
import models

# 头像图片源路径
AVATAR_SOURCE_DIR = Path("/Users/jianghaoqi/Pictures/当当和可乐/头像")
# 后端静态资源目录
BACKEND_STATIC_DIR = Path(__file__).parent / "static" / "avatars"

def migrate_data():
    db: Session = SessionLocal()
    
    try:
        # 读取初始数据
        data_file = Path(__file__).parent.parent / "docs" / "初始数据.json"
        with open(data_file, 'r', encoding='utf-8') as f:
            init_data = json.load(f)
        
        print("=" * 50)
        print("开始数据迁移...")
        print("=" * 50)
        
        # 获取所有猫咪
        cats_in_db = db.query(models.Cat).all()
        print(f"\n当前数据库中的猫咪: {[c.name for c in cats_in_db]}")
        
        # 准备静态资源目录
        BACKEND_STATIC_DIR.mkdir(parents=True, exist_ok=True)
        
        # 处理每只猫咪
        for cat_data in init_data["cats"]:
            cat_name = cat_data["name"]
            
            # 查找对应的猫咪
            cat = db.query(models.Cat).filter(models.Cat.name == cat_name).first()
            
            if not cat:
                print(f"\n⚠️  未找到猫咪: {cat_name}，跳过")
                continue
            
            print(f"\n处理猫咪: {cat_name}")
            print("-" * 40)
            
            # 更新猫咪基本信息
            cat.breed = cat_data["breed"]
            cat.birth_date = date.fromisoformat(cat_data["birth_date"])
            cat.neutered = cat_data["neutered"]
            
            # 复制头像并设置路径
            avatar_source = AVATAR_SOURCE_DIR / f"{cat_name}.jpg"
            if avatar_source.exists():
                # 复制头像到静态资源目录
                avatar_dest = BACKEND_STATIC_DIR / f"{cat_name}.jpg"
                shutil.copy2(avatar_source, avatar_dest)
                # 设置数据库中的头像路径
                cat.avatar = f"/static/avatars/{cat_name}.jpg"
                print(f"  ✅ 头像已设置: {avatar_dest}")
            else:
                print(f"  ⚠️  头像文件不存在: {avatar_source}")
            
            # 清除该猫咪的所有体重记录
            deleted = db.query(models.WeightRecord).filter(
                models.WeightRecord.cat_id == cat.id
            ).delete()
            print(f"  🗑️  已删除 {deleted} 条旧体重记录")
            
            # 导入新的体重记录
            new_records = 0
            for wr in cat_data["weight_records"]:
                weight_record = models.WeightRecord(
                    cat_id=cat.id,
                    date=date.fromisoformat(wr["date"]),
                    weight=wr["weight"]
                )
                db.add(weight_record)
                new_records += 1
            
            print(f"  ✅ 已导入 {new_records} 条新体重记录")
            print(f"  📊 体重范围: {cat_data['weight_records'][0]['weight']}g ~ {cat_data['weight_records'][-1]['weight']}g")
        
        # 提交更改
        db.commit()
        
        print("\n" + "=" * 50)
        print("✅ 数据迁移完成！")
        print("=" * 50)
        
        # 打印最终状态
        print("\n📊 最终状态:")
        for cat in db.query(models.Cat).all():
            weight_count = db.query(models.WeightRecord).filter(
                models.WeightRecord.cat_id == cat.id
            ).count()
            latest = db.query(models.WeightRecord).filter(
                models.WeightRecord.cat_id == cat.id
            ).order_by(models.WeightRecord.date.desc()).first()
            
            print(f"\n  {cat.name}:")
            print(f"    品种: {cat.breed}")
            print(f"    生日: {cat.birth_date}")
            print(f"    头像: {cat.avatar or '未设置'}")
            print(f"    体重记录数: {weight_count}")
            if latest:
                print(f"    最新体重: {latest.weight}g ({latest.date})")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_data()
