import sqlite3
import os
import threading
from pathlib import Path

# 🔥 καλύτερο για Render από relative path
DB_PATH = Path(os.environ.get("DB_PATH", "/tmp/mundial.db"))

# 🔥 lock για να αποφεύγεις concurrent writes
db_lock = threading.Lock()


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    # 🔥 IMPORTANT FIXES FOR SQLITE ON RENDER
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    return conn


def initialize_database():
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            points INTEGER DEFAULT 0,
            exact_scores INTEGER DEFAULT 0,
            correct_results INTEGER DEFAULT 0,
            correct_scorers INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            home_team TEXT,
            away_team TEXT,
            group_name TEXT,
            phase TEXT,
            kickoff TEXT,
            home_score INTEGER,
            away_score INTEGER,
            scorers TEXT,
            finished INTEGER DEFAULT 0,
            scored INTEGER DEFAULT 0
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_id INTEGER,
            match_id INTEGER,
            home_score INTEGER,
            away_score INTEGER,
            scorers TEXT,
            points INTEGER DEFAULT 0,
            UNIQUE(player_id, match_id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT,
            team_name TEXT
        )
        """)

        conn.commit()
        conn.close()


def create_user(username, password, role="player"):
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (?, ?, ?)
        """, (username, password, role))

        conn.commit()
        conn.close()


def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT * FROM users WHERE username=?
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    return user


def seed_players():
    with db_lock:
        conn = get_connection()
        cursor = conn.cursor()

        players = [
            "Alex",
            "George",
            "Panos",
            "Kle",
            "Vlasis",
            "Pets",
            "Vel"
        ]

        for p in players:
            try:
                cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
                """, (p, "1234", "player"))
            except:
                pass

        conn.commit()
        conn.close()