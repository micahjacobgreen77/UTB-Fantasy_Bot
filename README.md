# UTB Fantasy Bot 🤖⚾

An automated fantasy baseball alert bot that posts to X (Twitter) in real time when players on my roster hit a home run, steal a base, record a save, or earn a win.

## How it works

The bot checks live MLB game data every 15 minutes via the [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI). When a tracked player on my fantasy baseball team records an HR, SB, SV, or W, it automatically posts an alert to X with the player's name, team, and live scoreboard. It won't double-post — a state file keeps track of what's already been sent.

## Example posts

```
HR: Yordan Alvarez (HOU)
NYY 2, HOU 5 (Bottom 6)

SB: Andrés Giménez (TOR)
COL 1, TOR 5 (Middle 8)

SV: Edwin Díaz (NYM)
NYM 3, ATL 2 (Final)

W: Garrett Crochet (CWS)
CWS 4, DET 1 (Final)
```

## Stack

- Python 3.12
- [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI) — live game and player data
- [X API v2](https://developer.twitter.com/en/docs/twitter-api) — posting alerts via OAuth 1.0a
- GitHub Actions — runs the bot on a schedule, no server needed
- [cron-job.org](https://cron-job.org) — triggers the workflow every 15 minutes reliably

## Project structure

```
UTB-Fantasy_Bot/
├── fantasy_bot.py        # Main bot logic
├── roster.json           # Players being tracked
├── bot_state.json        # Tracks alerts already sent (auto-updated)
├── .github/
│   └── workflows/
│       └── bot.yml       # GitHub Actions workflow
└── .env                  # Local credentials (never committed)
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/micahjacobgreen77/UTB-Fantasy_Bot.git
cd UTB-Fantasy_Bot
```

### 2. Install dependencies
```bash
pip install MLB-StatsAPI requests python-dotenv requests-oauthlib
```

### 3. Add your credentials
Create a `.env` file:
```
POST_TO_X=true
API_KEY=your_consumer_key
API_SECRET=your_consumer_key_secret
ACCESS_TOKEN=your_access_token
ACCESS_TOKEN_SECRET=your_access_token_secret
```

### 4. Edit your roster
Update `roster.json` with the players you want to track.

### 5. Run locally (test mode)
Set `POST_TO_X=false` in `.env` to print alerts to the terminal without posting.
```bash
python fantasy_bot.py
```

## Automation

The bot is triggered every 15 minutes via [cron-job.org](https://cron-job.org), which calls the GitHub Actions `workflow_dispatch` endpoint. This replaces relying on GitHub's built-in cron scheduler, which is unreliable for frequent schedules.

Required GitHub Secrets:
- `API_KEY`
- `API_SECRET`
- `ACCESS_TOKEN`
- `ACCESS_TOKEN_SECRET`
- `GH_PAT` — a Personal Access Token with repo access (used to save bot state between runs)

## Updating the roster

Edit `roster.json` and push:
```bash
git add roster.json
git commit -m "update roster"
git push
```
