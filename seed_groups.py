

import os


print(os.environ["DATABASE_URL"])

from models.database import get_connection
import json

with open("data/groups.json", encoding="utf-8") as f:
    data = json.load(f)

conn = get_connection()
cursor = conn.cursor()

# καθάρισε παλιά groups (προαιρετικό)
cursor.execute("DELETE FROM groups")

for group in data["groups"]:

    group_name = group["name"].replace("Group ", "")

    for team in group["teams"]:

        cursor.execute("""
            INSERT INTO groups
            (group_name, team_name)
            VALUES (%s, %s)
        """, (
            group_name,
            team
        ))

conn.commit()
conn.close()

print("Groups imported successfully.")