#!/usr/bin/env python3
"""
数据库迁移脚本 - 修复字段名
将 coat_color 改为 color，添加 deworming_date 和 medical_history 字段
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "cat_care.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取现有表结构
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    existing_tables = {row[0] for row in cursor.fetchall()}
    
    print(f"现有表: {existing_tables}")
    
    # 获取 cats 表现有字段
    cursor.execute("PRAGMA table_info(cats)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"cats 表现有字段: {existing_columns}")
    
    # 1. 如果有 coat_color 字段，重命名为 color
    if 'coat_color' in existing_columns and 'color' not in existing_columns:
        print("重命名字段: coat_color -> color")
        # SQLite 不支持直接重命名列，需要重建表
        cursor.execute("""
            CREATE TABLE cats_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR,
                gender VARCHAR,
                breed VARCHAR,
                color VARCHAR,
                birth_date DATE,
                neutered BOOLEAN DEFAULT 0,
                vaccination_status VARCHAR,
                deworming_date DATE,
                medical_history TEXT,
                avatar VARCHAR,
                owner_id INTEGER,
                FOREIGN KEY(owner_id) REFERENCES users(id)
            )
        """)
        
        # 复制数据
        cursor.execute("""
            INSERT INTO cats_new (id, name, gender, breed, color, birth_date, neutered, 
                                  vaccination_status, avatar, owner_id)
            SELECT id, name, gender, breed, coat_color, birth_date, neutered, 
                   vaccination_status, avatar, owner_id
            FROM cats
        """)
        
        # 删除旧表，重命名新表
        cursor.execute("DROP TABLE cats")
        cursor.execute("ALTER TABLE cats_new RENAME TO cats")
        print("cats 表重建完成")
    
    # 2. 添加缺失的字段
    cats_columns = [
        ("color", "VARCHAR"),
        ("deworming_date", "DATE"),
        ("medical_history", "TEXT"),
    ]
    
    cursor.execute("PRAGMA table_info(cats)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    for col_name, col_type in cats_columns:
        if col_name not in existing_columns:
            print(f"添加字段: cats.{col_name}")
            cursor.execute(f"ALTER TABLE cats ADD COLUMN {col_name} {col_type}")
    
    conn.commit()
    conn.close()
    print("迁移完成!")

if __name__ == "__main__":
    migrate()
