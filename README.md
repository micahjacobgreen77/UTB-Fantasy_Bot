# UTB Fantasy Bot 🤖⚾

An automated fantasy baseball alert bot that posts to X (Twitter) in real time when players on my roster hit a home run, steal a base, or record a save.

## How it works

The bot checks live MLB game data every 15 minutes via the [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI). When a tracked player on my fantasy baseball team records an HR, SB, or SV, it automatically posts an alert to X with the player's name, team, and live scoreboard. It won't double-post — a state file keeps track of what's already been sent.

## Example posts

```
HR: Yordan Alvarez (HOU)
NYY 2, HOU 5 (Bottom 6)

SB: Andrés Giménez (TOR)
COL 1, TOR 5 (Middle 8)

SV: Edwin Díaz (NYM)
NYM 3, ATL 2 (Final)
```

## Stack

- Python 3.12
- [MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI) — live game and player data
- [X API v2](https://developer.twitter.com/en/docs/twitter-api) — posting alerts via OAuth 1.0a
- GitHub Actions — runs every 5 minutes automatically, no server needed

## Project structure

```
utb-fantasy-bot/
├── fantasy_bot.py        # Main bot logic
├── roster.json           # Players being tracked
├── bot_state.json        # Tracks alerts already sent (auto-updated)
├── .github/
│   └── workflows/
│       └── bot.yml       # GitHub Actions schedule
└── .env                  # Local credentials (never committed)
```

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/utb-fantasy-bot.git
cd utb-fantasy-bot
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

## Automation via GitHub Actions

The bot runs automatically every 15 minutes via GitHub Actions. No server required.

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

