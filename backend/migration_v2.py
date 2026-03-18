#!/usr/bin/env python3
"""
数据库迁移脚本 - 迭代2
添加新表和新字段
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
    
    # 1. 为 cats 表添加新字段
    cats_columns = [
        ("coat_color", "VARCHAR"),
        ("vaccination_status", "VARCHAR"),
        ("last_internal_deworming", "DATE"),
        ("last_external_deworming", "DATE"),
    ]
    
    cursor.execute("PRAGMA table_info(cats)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"cats 表现有字段: {existing_columns}")
    
    for col_name, col_type in cats_columns:
        if col_name not in existing_columns:
            print(f"添加字段: cats.{col_name}")
            cursor.execute(f"ALTER TABLE cats ADD COLUMN {col_name} {col_type}")
    
    # 2. 创建 medical_histories 表
    if "medical_histories" not in existing_tables:
        print("创建表: medical_histories")
        cursor.execute("""
            CREATE TABLE medical_histories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_id INTEGER NOT NULL,
                disease VARCHAR NOT NULL,
                date DATE NOT NULL,
                treatment TEXT,
                notes TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cat_id) REFERENCES cats(id)
            )
        """)
    
    # 3. 创建 albums 表
    if "albums" not in existing_tables:
        print("创建表: albums")
        cursor.execute("""
            CREATE TABLE albums (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_id INTEGER NOT NULL,
                name VARCHAR NOT NULL,
                cover_photo_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cat_id) REFERENCES cats(id),
                FOREIGN KEY(cover_photo_id) REFERENCES photos(id)
            )
        """)
    
    # 4. 创建 photos 表
    if "photos" not in existing_tables:
        print("创建表: photos")
        cursor.execute("""
            CREATE TABLE photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cat_id INTEGER NOT NULL,
                album_id INTEGER,
                url VARCHAR NOT NULL,
                thumbnail VARCHAR,
                description TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(cat_id) REFERENCES cats(id),
                FOREIGN KEY(album_id) REFERENCES albums(id)
            )
        """)
    
    # 如果 photos 表刚创建，需要更新 albums 表的外键引用
    # SQLite 不支持 ALTER TABLE ADD FOREIGN KEY，所以这个引用在创建时处理
    
    conn.commit()
    conn.close()
    print("迁移完成!")

if __name__ == "__main__":
    migrate()
