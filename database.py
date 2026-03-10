import sqlite3

DB_NAME = "tasks.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        fullname TEXT,
        hashed_password TEXT
    )
    """
    )
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        priority TEXT,
        tags TEXT,
        owner TEXT,
        FOREIGN KEY(owner) REFERENCES users(username)
    )
    """
    )

    conn.commit()
    conn.close()
