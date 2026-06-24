# init_db.py
# 增添多会话支持和评分
# init_db.py（更新版）
import sqlite3
from pathlib import Path

DB_PATH = Path("***.db")

def init_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # 聊天记录表（新增 rating 字段）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            rating INTEGER,                -- 新增：0=未评, 1=不好, 2=一般, 3=好
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_session ON chat_history(user_id, session_id);')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_rating ON chat_history(rating);')

    conn.commit()
    conn.close()
    print("✅ 数据库已升级（支持评分）")

if __name__ == "__main__":
    init_database()
