# AI Sports Assistant

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Jupyter](https://img.shields.io/badge/Notebook-Jupyter-orange.svg)](https://jupyter.org/)
[![Scikit-learn](https://img.shields.io/badge/ML-scikit--learn-f7931e.svg)](https://scikit-learn.org/)
[![Status](https://img.shields.io/badge/Status-Runnable-success.svg)](#quick-start)

A GitHub-ready AI project that reminds users about upcoming matches, scores match importance, supports natural-language queries, adds predictive insights, and now supports live football fixtures plus email delivery.

## Project Story
Sports reminder apps usually stop at calendar alerts: they tell you *when* a game happens, but not *why it matters*.  
This project turns match reminders into an AI-assisted fan experience:
- It identifies high-stakes games (derbies, knockout fixtures, top-4 pressure).
- It adds contextual intelligence (form streaks, momentum, must-win framing).
- It supports natural-language interaction for quick answers.
- It includes predictive insights with explainable reasoning.

## Features
- Live football fixture ingestion via `football-data.org` with sample-data fallback
- Upcoming match reminders (1 day and 1 hour before)
- Match info: opponent, competition, kickoff time
- AI-style importance scoring (`low`, `medium`, `high`)
- Context-aware insights (form streak, must-win signals)
- Natural language queries (e.g., "When is Milan's next match?")
- Match outcome prediction + explanation of prediction drivers
- Email notification delivery for due reminders via SMTP

## Project Structure
- `src/data_ingestion.py`: live football-data.org integration plus sample fallback ingestion
- `src/importance_engine.py`: match importance scoring
- `src/reminder_scheduler.py`: reminder generation plus SMTP email delivery
- `src/nl_interface.py`: natural language query helper
- `src/prediction_engine.py`: simple ML prediction + explanations
- `notebooks/`: runnable notebooks for each component

## Demo Flow
1. Load fixtures + recent form from live API or local sample fallback.
2. Score match importance and generate context-aware insights.
3. Build personalized reminders (1 day and 1 hour before).
4. Deliver due reminders by email.
5. Ask natural-language questions like:
   - "When is Milan's next match?"
   - "Remind me only for big matches"
6. Predict win probability and explain the model decision.

## Quick Start
1. Create environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Optional: configure live data + email secrets:
   ```bash
   export FOOTBALL_DATA_API_TOKEN="your-football-data-token"
   export FOOTBALL_DATA_TEAM_ID="98"
   export SMTP_HOST="smtp.gmail.com"
   export SMTP_PORT="587"
   export SMTP_USERNAME="your-email@example.com"
   export SMTP_PASSWORD="your-app-password"
   export SPORTS_EMAIL_FROM="your-email@example.com"
   export SPORTS_EMAIL_TO="recipient@example.com"
   ```
3. Launch Jupyter:
   ```bash
   jupyter notebook
   ```
4. Run notebooks in order:
   - `notebooks/01_data_pipeline.ipynb`
   - `notebooks/02_importance_scoring.ipynb`
   - `notebooks/03_reminder_simulation.ipynb`
   - `notebooks/04_nl_queries.ipynb`
   - `notebooks/05_match_prediction.ipynb`
   - `notebooks/06_explain_predictions.ipynb`

## Live Data Example
Use a club id from the official [`football-data.org` docs](https://docs.football-data.org/general/v4/team.html) and load real fixtures:

```python
import os

from src.data_ingestion import TeamProfile, compute_streak, load_recent_form, load_upcoming_fixtures
from src.importance_engine import score_match_importance

profile = TeamProfile(team="AC Milan", league="Serie A", team_id=int(os.environ["FOOTBALL_DATA_TEAM_ID"]))
fixtures = load_upcoming_fixtures(profile=profile, prefer_live=True)
recent_form = load_recent_form(profile=profile, prefer_live=True)
streak = compute_streak(recent_form)
scored = score_match_importance(fixtures, current_rank=4, target_rank=4, streak=streak)
```

## Email Delivery Example
Send reminders that are currently due:

```python
from src.reminder_scheduler import EmailConfig, ReminderPreference, build_reminder_rows, send_email_notifications

preferences = ReminderPreference(remind_day_before=True, remind_hour_before=True, only_big_matches=False)
reminders = build_reminder_rows(scored, preferences)
delivery_log = send_email_notifications(reminders, EmailConfig.from_env(), dry_run=True)
delivery_log
```

Set `dry_run=False` when your SMTP settings are ready and you want to actually send the emails.


## Next Version Ideas
- Add Telegram/Discord notification delivery alongside email
- Add player-level performance modeling with richer features
- Build a lightweight web UI for user preferences and chat

## Notes
- The project still works without secrets because it automatically falls back to local sample data.
- Live data uses the `X-Auth-Token` header expected by `football-data.org`.
- Many email providers require an app password rather than your normal login password.
