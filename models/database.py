import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(
        DATABASE_URL,
        cursor_factory=RealDictCursor
    )


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
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
        id SERIAL PRIMARY KEY,
        group_name TEXT,
        team_name TEXT
    )
    """)

    conn.commit()
    conn.close()


# ---------------- USERS ----------------

def create_user(username, password, role="player"):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users (username, password, role)
        VALUES (%s, %s, %s)
    """, (username, password, role))

    conn.commit()
    conn.close()


def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT * FROM users WHERE username=%s
    """, (username,))

    user = cursor.fetchone()
    conn.close()

    return user


# ---------------- SEED ----------------

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
            cursor.execute("""
                INSERT INTO users (username, password, role)
                VALUES (%s, %s, %s)
            """, (p, "1234", "player"))
        except:
            pass

    conn.commit()
    conn.close()