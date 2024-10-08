import sqlite3

conn = sqlite3.connect("users.db", timeout=10)
cursor = conn.cursor()

# Проверяем наличие колонки coins и добавляем ее, если ее нет
cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]
if "coins" not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN coins INTEGER DEFAULT 500")

# Создаем таблицу заново с правильной структурой, если она не существует
cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    coins INTEGER DEFAULT 500
)
"""
)

conn.commit()
conn.close()
