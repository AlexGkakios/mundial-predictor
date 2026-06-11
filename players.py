import json

with open("data/players.json", "r", encoding="utf-8") as f:
    data = json.load(f)

players = data["stickers"]


def is_valid_player(p):
    return (
        isinstance(p, dict)
        and p.get("name") not in ["Emblem", "Team Photo"]
    )


def get_players_by_team(team_name):
    return [
        p for p in players
        if isinstance(p, dict)
        and p.get("team") == team_name
        and is_valid_player(p)
    ]