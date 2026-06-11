import json

with open("data/players.json", encoding="utf-8") as f:
    players_data = json.load(f)

def is_valid_player(player):
    bad_names = ["Emblem", "Team Photo"]
    return player["name"] not in bad_names

def get_players_by_team(team_name):
    return [
        p for p in players_data
        if p["team"] == team_name and is_valid_player(p)
    ]