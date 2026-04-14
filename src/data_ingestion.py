from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd


DEFAULT_TZ = "America/Los_Angeles"


@dataclass
class TeamProfile:
    team: str
    league: str = "Serie A"


def sample_upcoming_fixtures(team: str = "AC Milan", tz: str = DEFAULT_TZ) -> pd.DataFrame:
    """Create sample upcoming fixtures so the project runs without external APIs."""
    now = datetime.now(ZoneInfo(tz)).replace(minute=0, second=0, microsecond=0)

    fixtures = [
        {
            "team": team,
            "opponent": "Inter Milan",
            "competition": "Serie A",
            "kickoff": now + timedelta(days=2, hours=4),
            "is_derby": 1,
            "is_knockout": 0,
            "home": 0,
        },
        {
            "team": team,
            "opponent": "Juventus",
            "competition": "Coppa Italia",
            "kickoff": now + timedelta(days=5, hours=1),
            "is_derby": 0,
            "is_knockout": 1,
            "home": 1,
        },
        {
            "team": team,
            "opponent": "Napoli",
            "competition": "Serie A",
            "kickoff": now + timedelta(days=8, hours=3),
            "is_derby": 0,
            "is_knockout": 0,
            "home": 1,
        },
        {
            "team": team,
            "opponent": "PSG",
            "competition": "Champions League",
            "kickoff": now + timedelta(days=12, hours=2),
            "is_derby": 0,
            "is_knockout": 1,
            "home": 0,
        },
    ]

    df = pd.DataFrame(fixtures)
    df["kickoff"] = pd.to_datetime(df["kickoff"])
    return df.sort_values("kickoff").reset_index(drop=True)


def sample_recent_form(team: str = "AC Milan") -> pd.DataFrame:
    """Create sample recent-form stats for context-aware insights."""
    rows = [
        {"team": team, "match": "vs Lazio", "result": "W", "goals_for": 2, "goals_against": 1, "xg_for": 1.8, "xg_against": 0.9},
        {"team": team, "match": "vs Roma", "result": "W", "goals_for": 3, "goals_against": 1, "xg_for": 2.1, "xg_against": 0.8},
        {"team": team, "match": "vs Atalanta", "result": "W", "goals_for": 1, "goals_against": 0, "xg_for": 1.2, "xg_against": 0.6},
        {"team": team, "match": "vs Fiorentina", "result": "D", "goals_for": 1, "goals_against": 1, "xg_for": 1.0, "xg_against": 1.1},
        {"team": team, "match": "vs Torino", "result": "L", "goals_for": 0, "goals_against": 1, "xg_for": 0.7, "xg_against": 1.3},
    ]
    return pd.DataFrame(rows)


def compute_streak(form_df: pd.DataFrame) -> int:
    """Positive for win streak, negative for losing streak, 0 for mixed/no streak."""
    streak = 0
    for result in form_df["result"].tolist():
        if result == "W":
            if streak >= 0:
                streak += 1
            else:
                break
        elif result == "L":
            if streak <= 0:
                streak -= 1
            else:
                break
        else:
            break
    return streak


def save_csv(df: pd.DataFrame, path: str) -> None:
    df.to_csv(path, index=False)
