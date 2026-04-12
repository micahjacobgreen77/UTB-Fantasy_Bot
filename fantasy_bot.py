import json
import os
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

import requests
import statsapi
from requests_oauthlib import OAuth1
from dotenv import load_dotenv

load_dotenv()

ROSTER_FILE = "roster.json"
STATE_FILE = "bot_state.json"

# X (Twitter) OAuth 1.0a credentials
API_KEY = os.getenv("API_KEY", "")
API_SECRET = os.getenv("API_SECRET", "")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN", "")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET", "")

POST_TO_X = os.getenv("POST_TO_X", "false").lower() == "true"

ET = ZoneInfo("America/New_York")


def load_roster() -> dict:
    with open(ROSTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state() -> dict:
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"alerts_sent": []}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def safe_int(value, default=0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def get_et_dates() -> list[str]:
    """Return today and yesterday in ET to avoid missing late West Coast games."""
    now_et = datetime.now(ET)
    today = now_et.strftime("%Y-%m-%d")
    yesterday = (now_et - timedelta(days=1)).strftime("%Y-%m-%d")
    return [today, yesterday]


def post_to_x(text: str) -> None:
    if not POST_TO_X:
        print("\n--- TEST POST ---")
        print(text)
        print("-----------------\n")
        return

    if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET]):
        raise ValueError("Missing one or more X credentials in .env")

    url = "https://api.twitter.com/2/tweets"
    auth = OAuth1(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    payload = {"text": text}

    response = requests.post(url, auth=auth, json=payload, timeout=30)
    response.raise_for_status()
    print("Posted:", response.json())


def find_player_id(player_name: str) -> Optional[int]:
    results = statsapi.lookup_player(player_name)
    if not results:
        return None
    return results[0].get("id")


def build_player_id_map(player_names: list[str]) -> dict[int, str]:
    id_map = {}
    for name in player_names:
        pid = find_player_id(name)
        if pid:
            id_map[pid] = name
        else:
            print(f"Warning: could not find player ID for {name}")
    return id_map


def get_schedule_for_date(date_str: str) -> list[dict]:
    return statsapi.schedule(date=date_str)


def get_boxscore(game_id: int) -> dict:
    return statsapi.get("game_boxscore", {"gamePk": game_id})


def get_live_game_context(game_id: int) -> dict:
    data = statsapi.get("game", {"gamePk": game_id})
    game_data = data.get("gameData", {})
    live_data = data.get("liveData", {})
    linescore = live_data.get("linescore", {}) or {}

    home_team = game_data.get("teams", {}).get("home", {}).get("abbreviation", "HOME")
    away_team = game_data.get("teams", {}).get("away", {}).get("abbreviation", "AWAY")

    home_score = linescore.get("teams", {}).get("home", {}).get("runs", 0)
    away_score = linescore.get("teams", {}).get("away", {}).get("runs", 0)

    inning = linescore.get("currentInning", "")
    inning_state = linescore.get("inningState", "")

    return {
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "inning": inning,
        "inning_state": inning_state,
    }


def format_scoreboard(context: dict) -> str:
    inning_state = context["inning_state"]
    inning = context["inning"]

    inning_text = f"{inning_state} {inning}".strip()
    if not inning_text:
        inning_text = "Live"

    return (
        f"{context['away_team']} {context['away_score']}, "
        f"{context['home_team']} {context['home_score']} "
        f"({inning_text})"
    )


def make_hr_alert(name: str, player_team: str, context: dict, total_hr: int) -> str:
    scoreboard = format_scoreboard(context)
    if total_hr == 1:
        return f"HR: {name} ({player_team})\n{scoreboard}"
    return f"HR: {name} ({player_team}) x{total_hr}\n{scoreboard}"


def make_sb_alert(name: str, player_team: str, context: dict, total_sb: int) -> str:
    scoreboard = format_scoreboard(context)
    if total_sb == 1:
        return f"SB: {name} ({player_team})\n{scoreboard}"
    return f"SB: {name} ({player_team}) x{total_sb}\n{scoreboard}"


def make_save_alert(name: str, player_team: str, context: dict) -> str:
    scoreboard = format_scoreboard(context)
    return f"SV: {name} ({player_team})\n{scoreboard}"


def make_win_alert(name: str, player_team: str, context: dict) -> str:
    scoreboard = format_scoreboard(context)
    return f"W: {name} ({player_team})\n{scoreboard}"


def get_all_tracked_entries(date_str: str, tracked_ids: set[int]) -> list[dict]:
    entries = []
    games = get_schedule_for_date(date_str)

    for game in games:
        game_id = game.get("game_id")
        if not game_id:
            continue

        try:
            box = get_boxscore(game_id)
        except Exception as e:
            print(f"Skipping game {game_id}: {e}")
            continue

        teams = box.get("teams", {})
        for side in ("home", "away"):
            team = teams.get(side, {})
            team_abbrev = team.get("team", {}).get("abbreviation", side.upper())
            players = team.get("players", {})

            for _, pdata in players.items():
                person = pdata.get("person", {})
                pid = person.get("id")

                if pid not in tracked_ids:
                    continue

                entries.append({
                    "game_id": game_id,
                    "player_id": pid,
                    "name": person.get("fullName", ""),
                    "team_abbrev": team_abbrev,
                    "date_str": date_str,
                    "batting": pdata.get("stats", {}).get("batting", {}) or {},
                    "pitching": pdata.get("stats", {}).get("pitching", {}) or {},
                })

    return entries


def run_live_alerts() -> None:
    roster = load_roster()
    state = load_state()

    player_id_map = build_player_id_map(roster["players"])
    tracked_ids = set(player_id_map.keys())

    # Check both today and yesterday in ET to catch late West Coast games
    dates = get_et_dates()
    all_entries = []
    seen_game_player = set()

    for date_str in dates:
        for entry in get_all_tracked_entries(date_str, tracked_ids):
            key = (entry["game_id"], entry["player_id"])
            if key not in seen_game_player:
                seen_game_player.add(key)
                all_entries.append(entry)

    for entry in all_entries:
        pid = entry["player_id"]
        name = entry["name"]
        game_id = entry["game_id"]
        team_abbrev = entry["team_abbrev"]
        date_str = entry["date_str"]
        batting = entry["batting"]
        pitching = entry["pitching"]

        hr = safe_int(batting.get("homeRuns"))
        sb = safe_int(batting.get("stolenBases"))
        saves = safe_int(pitching.get("saves"))
        wins = safe_int(pitching.get("wins"))

        try:
            context = get_live_game_context(game_id)
        except Exception:
            context = {
                "away_team": "AWAY",
                "away_score": 0,
                "home_team": "HOME",
                "home_score": 0,
                "inning_state": "Live",
                "inning": "",
            }

        if hr > 0:
            unique_key = f"{date_str}|hr|{pid}|{hr}"
            if unique_key not in state["alerts_sent"]:
                post_to_x(make_hr_alert(name, team_abbrev, context, hr))
                state["alerts_sent"].append(unique_key)

        if sb > 0:
            unique_key = f"{date_str}|sb|{pid}|{sb}"
            if unique_key not in state["alerts_sent"]:
                post_to_x(make_sb_alert(name, team_abbrev, context, sb))
                state["alerts_sent"].append(unique_key)

        if saves > 0:
            unique_key = f"{date_str}|save|{pid}|{saves}"
            if unique_key not in state["alerts_sent"]:
                post_to_x(make_save_alert(name, team_abbrev, context))
                state["alerts_sent"].append(unique_key)

        if wins > 0:
            unique_key = f"{date_str}|win|{pid}|{wins}"
            if unique_key not in state["alerts_sent"]:
                post_to_x(make_win_alert(name, team_abbrev, context))
                state["alerts_sent"].append(unique_key)

    save_state(state)


if __name__ == "__main__":
    run_live_alerts()
