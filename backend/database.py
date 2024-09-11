import sqlite3

def get_db():
    conn = sqlite3.connect('users.db')
    conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            UUID TEXT UNIQUE,
            email TEXT UNIQUE,
            username TEXT UNIQUE,
            hashed_password TEXT,
            role TEXT
        );
    ''')
    return conn
