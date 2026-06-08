import json

import os

os.environ["DATABASE_URL"] = "postgresql://mundial_db_yyp2_user:P80jpEg6UsDpwnQtrN2HfoDeqTDohs6I@dpg-d8ir50ek1jcs73apgt5g-a.frankfurt-postgres.render.com/mundial_db_yyp2"

from models.database import get_connection

with open("data/matches.json", "r", encoding="utf-8") as f:
    data = json.load(f)

conn = get_connection()
cursor = conn.cursor()

cursor.execute("DELETE FROM matches")

for match in data["matches"]:
    from datetime import datetime, timedelta
    date = match["date"]
    date = match["date"]

    time_part = match["time"].split(" ")[0]
    utc_part = match["time"].split(" ")[1]

    dt = datetime.strptime(
        f"{date} {time_part}",
        "%Y-%m-%d %H:%M"
    )

    offset = int(utc_part.replace("UTC", ""))

    # μετατροπή σε UTC
    dt = dt - timedelta(hours=offset)

    # UTC -> Ελλάδα (UTC+3)
    dt = dt + timedelta(hours=3)

    kickoff = dt.strftime("%Y-%m-%d %H:%M")

    cursor.execute("""
        INSERT INTO matches
        (
            home_team,
            away_team,
            group_name,
            phase,
            kickoff
        )
        VALUES (%s,%s,%s,%s,%s)
    """, (
        match["team1"],
        match["team2"],
        match["group"],
        match["round"],
        kickoff
    ))

conn.commit()
conn.close()

print("Matches imported successfully.")