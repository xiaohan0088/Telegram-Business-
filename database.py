import sqlite3
import os

# 创建 SQL 文件夹
DB_DIR = 'SQL'
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

FINANCE_DB = os.path.join(DB_DIR, 'finance.db')
CACHE_DB = os.path.join(DB_DIR, 'msg_cache.db')

def init_all_db():
    with sqlite3.connect(FINANCE_DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, is_authorized INTEGER DEFAULT 0)')
        conn.execute('CREATE TABLE IF NOT EXISTS customer_settings (chat_id INTEGER PRIMARY KEY, currency TEXT DEFAULT "$", balance REAL DEFAULT 0)')
        conn.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY AUTOINCREMENT, chat_id INTEGER, type TEXT, amount REAL, currency TEXT, time TEXT)')
        # 新增：记录已反诈检测过的用户
        conn.execute('CREATE TABLE IF NOT EXISTS fanzha_log (user_id INTEGER PRIMARY KEY)')
        
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS cache (msg_id INTEGER PRIMARY KEY, chat_id INTEGER, chat_name TEXT, user_id INTEGER, text TEXT, time TEXT)')

def is_fanzha_checked(user_id):
    with sqlite3.connect(FINANCE_DB) as conn:
        row = conn.execute("SELECT user_id FROM fanzha_log WHERE user_id = ?", (user_id,)).fetchone()
        return True if row else False

def mark_fanzha_checked(user_id):
    with sqlite3.connect(FINANCE_DB) as conn:
        conn.execute("INSERT OR IGNORE INTO fanzha_log (user_id) VALUES (?)", (user_id,))