import sqlite3
from threading import Lock
import os

# Блокировка для безопасного доступа к базе данных из разных потоков
db_lock = Lock()

# Путь к папке для загрузки фотографий
UPLOAD_DIR = 'static/uploads/'
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db_connection():
    conn = sqlite3.connect('dating_app.db', check_same_thread=False)
    return conn


def get_db_cursor(conn):
    return conn.cursor()


def init_db():
    conn = get_db_connection()
    cursor = get_db_cursor(conn)

    # Проверка существования столбца gender и добавление его, если он отсутствует
    cursor.execute("PRAGMA table_info(profiles)")
    columns = [column[1] for column in cursor.fetchall()]
    if 'gender' not in columns:
        cursor.execute('ALTER TABLE profiles ADD COLUMN gender TEXT NOT NULL DEFAULT "не указано"')

    # Создание таблиц, если они не существуют
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            bio TEXT NOT NULL,
            photo TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            user_id INTEGER,
            liked_user_id INTEGER,
            PRIMARY KEY (user_id, liked_user_id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS dislikes (
            user_id INTEGER,
            disliked_user_id INTEGER,
            PRIMARY KEY (user_id, disliked_user_id)
        )
    ''')
    conn.commit()
    conn.close()


def save_profile(user_id, name, age, gender, bio, photo_path):
    with db_lock:
        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        cursor.execute(
            'INSERT OR REPLACE INTO profiles (user_id, name, age, gender, bio, photo) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, age, gender, bio, photo_path))
        conn.commit()
        conn.close()


def get_profile(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        cursor.execute('SELECT * FROM profiles WHERE user_id = ?', (user_id,))
        profile = cursor.fetchone()
        conn.close()
    return profile


def search_profiles(user_id, min_age, max_age, gender):
    with db_lock:
        conn = get_db_connection()
        cursor = get_db_cursor(conn)
        query = 'SELECT * FROM profiles WHERE user_id != ? AND age BETWEEN ? AND ?'
        params = [user_id, min_age, max_age]
        if gender != 'не важно':
            query += ' AND gender = ?'
            params.append(gender)
        cursor.execute(query, params)
        profiles = cursor.fetchall()
        conn.close()
    return profiles


def get_user_photo_path(user_id):
    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    photo_path = os.path.join(user_dir, f'{user_id}.jpg')
    return photo_path
