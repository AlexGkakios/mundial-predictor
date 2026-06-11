import json

with open("players.json", "r", encoding="utf-8") as f:
    players = json.load(f)


def get_players_by_team(team_name):
    return [
        p for p in players
        if isinstance(p, dict)
        and p.get("teamId") == team_name
    ]