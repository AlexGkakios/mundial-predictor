from models.database import get_connection

def reset_all():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Delete predictions
    cursor.execute("DELETE FROM predictions")

    # 2. Reset users leaderboard stats
    cursor.execute("""
        UPDATE users
        SET points = 0,
            exact_scores = 0,
            correct_results = 0,
            correct_scorers = 0
    """)

    # 3. Reset matches (un-finish games)
    cursor.execute("""
        UPDATE matches
        SET finished = 0,
            home_score = NULL,
            away_score = NULL,
            scorers = NULL
    """)

    conn.commit()
    conn.close()

    print("✅ FULL RESET COMPLETED")

if __name__ == "__main__":
    confirm = input("Are you sure you want FULL RESET? (yes/no): ")

    if confirm.lower() == "yes":
        reset_all()
    else:
        print("❌ Cancelled")