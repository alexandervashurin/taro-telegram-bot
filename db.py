import sqlite3
from contextlib import closing
from datetime import datetime
import pytz

tz = pytz.timezone('Asia/Yekaterinburg')

def get_db_connection():
    return sqlite3.connect('users.db')

def create_table():
    with closing(get_db_connection()) as conn:
        with conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    subscription_time TEXT
                )
            ''')

def write_user_to_db(user_id: int, username: str):
    current_time = datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S")
    with closing(get_db_connection()) as conn:
        with conn:
            conn.execute('''
                INSERT OR IGNORE INTO users (user_id, username, subscription_time)
                VALUES (?, ?, ?)
            ''', (user_id, username, current_time))

def read_users_from_db():
    with closing(get_db_connection()) as conn:
        with conn:
            cursor = conn.execute('SELECT * FROM users')
            return cursor.fetchall()

