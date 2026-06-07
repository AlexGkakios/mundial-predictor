import sqlite3
from pathlib import Path

DB_PATH = Path("database/mundial.db")


def get_connection():
    conn = sqlite3.connect(
        DB_PATH,
        timeout=30,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def initialize_database():

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

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO users
        (username,password,role)
        VALUES (?,?,?)
        """,
        (username, password, role)
    )

    conn.commit()
    conn.close()


def get_user(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM users
        WHERE username=?
        """,
        (username,)
    )

    user = cursor.fetchone()

    conn.close()

    return user


def seed_players():
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
            cursor.execute(
                "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                (p, "1234", "player")
            )
        except:
            pass

    conn.commit()
    conn.close()