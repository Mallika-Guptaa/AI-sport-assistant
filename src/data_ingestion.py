from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import pandas as pd


DEFAULT_TZ = "America/Los_Angeles"
FOOTBALL_DATA_BASE_URL = "https://api.football-data.org/v4"
DEFAULT_LOOKAHEAD_DAYS = 14
DEFAULT_RECENT_MATCH_LIMIT = 5

DERBY_RIVALS = {
    "ac milan": {"inter milan", "inter"},
    "inter milan": {"ac milan", "milan"},
    "arsenal": {"tottenham hotspur", "tottenham"},
    "tottenham hotspur": {"arsenal"},
    "real madrid": {"atletico madrid"},
    "atletico madrid": {"real madrid"},
    "manchester united": {"manchester city", "liverpool"},
    "manchester city": {"manchester united"},
    "lazio": {"roma"},
    "roma": {"lazio"},
}


@dataclass
class TeamProfile:
    team: str
    league: str = "Serie A"
    team_id: int | None = None


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
            "source": "sample",
        },
        {
            "team": team,
            "opponent": "Juventus",
            "competition": "Coppa Italia",
            "kickoff": now + timedelta(days=5, hours=1),
            "is_derby": 0,
            "is_knockout": 1,
            "home": 1,
            "source": "sample",
        },
        {
            "team": team,
            "opponent": "Napoli",
            "competition": "Serie A",
            "kickoff": now + timedelta(days=8, hours=3),
            "is_derby": 0,
            "is_knockout": 0,
            "home": 1,
            "source": "sample",
        },
        {
            "team": team,
            "opponent": "PSG",
            "competition": "Champions League",
            "kickoff": now + timedelta(days=12, hours=2),
            "is_derby": 0,
            "is_knockout": 1,
            "home": 0,
            "source": "sample",
        },
    ]

    df = pd.DataFrame(fixtures)
    df["kickoff"] = pd.to_datetime(df["kickoff"])
    return df.sort_values("kickoff").reset_index(drop=True)


def sample_recent_form(team: str = "AC Milan") -> pd.DataFrame:
    """Create sample recent-form stats for context-aware insights."""
    rows = [
        {"team": team, "match": "vs Lazio", "result": "W", "goals_for": 2, "goals_against": 1, "xg_for": 1.8, "xg_against": 0.9, "source": "sample"},
        {"team": team, "match": "vs Roma", "result": "W", "goals_for": 3, "goals_against": 1, "xg_for": 2.1, "xg_against": 0.8, "source": "sample"},
        {"team": team, "match": "vs Atalanta", "result": "W", "goals_for": 1, "goals_against": 0, "xg_for": 1.2, "xg_against": 0.6, "source": "sample"},
        {"team": team, "match": "vs Fiorentina", "result": "D", "goals_for": 1, "goals_against": 1, "xg_for": 1.0, "xg_against": 1.1, "source": "sample"},
        {"team": team, "match": "vs Torino", "result": "L", "goals_for": 0, "goals_against": 1, "xg_for": 0.7, "xg_against": 1.3, "source": "sample"},
    ]
    return pd.DataFrame(rows)


def _normalise_team_name(name: str) -> str:
    return name.strip().lower()


def _resolve_team_id(profile: TeamProfile) -> int | None:
    if profile.team_id is not None:
        return profile.team_id

    raw_value = os.getenv("FOOTBALL_DATA_TEAM_ID")
    if not raw_value:
        return None
    return int(raw_value)


def _is_derby(team: str, opponent: str) -> int:
    rivals = DERBY_RIVALS.get(_normalise_team_name(team), set())
    return int(_normalise_team_name(opponent) in rivals)


def _is_knockout_match(match: dict[str, Any]) -> int:
    competition = match.get("competition", {})
    stage = str(match.get("stage", "")).upper()
    competition_type = str(competition.get("type", "")).upper()
    return int(
        competition_type == "CUP"
        or any(token in stage for token in ["PLAYOFF", "KNOCKOUT", "LAST_", "SEMI", "FINAL"])
    )


def _football_data_request(path: str, api_token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    query = f"?{urlencode(params)}" if params else ""
    request = Request(
        f"{FOOTBALL_DATA_BASE_URL}{path}{query}",
        headers={
            "X-Auth-Token": api_token,
            "User-Agent": "ai-sports-assistant/1.0",
        },
    )

    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"football-data API error {exc.code}: {detail or exc.reason}") from exc
    except URLError as exc:
        raise RuntimeError(f"football-data API connection error: {exc.reason}") from exc


def fetch_live_upcoming_fixtures(
    profile: TeamProfile,
    api_token: str,
    tz: str = DEFAULT_TZ,
    lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> pd.DataFrame:
    """Fetch upcoming fixtures from football-data.org for a specific club."""
    team_id = _resolve_team_id(profile)
    if team_id is None:
        raise ValueError("Live fixture ingestion requires TeamProfile.team_id.")

    start = datetime.now(ZoneInfo("UTC")).date()
    end = start + timedelta(days=lookahead_days)
    payload = _football_data_request(
        f"/teams/{team_id}/matches",
        api_token=api_token,
        params={
            "dateFrom": start.isoformat(),
            "dateTo": end.isoformat(),
            "status": "SCHEDULED",
            "limit": 100,
        },
    )

    rows: list[dict[str, Any]] = []
    local_tz = ZoneInfo(tz)

    for match in payload.get("matches", []):
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        is_home = int(home_team.get("id") == team_id)
        opponent = away_team.get("name") if is_home else home_team.get("name")
        kickoff = pd.Timestamp(match["utcDate"], tz="UTC").tz_convert(local_tz)
        rows.append(
            {
                "team": profile.team,
                "opponent": opponent,
                "competition": match.get("competition", {}).get("name", profile.league),
                "kickoff": kickoff,
                "is_derby": _is_derby(profile.team, opponent),
                "is_knockout": _is_knockout_match(match),
                "home": is_home,
                "source": "football-data.org",
            }
        )

    if not rows:
        return pd.DataFrame(columns=["team", "opponent", "competition", "kickoff", "is_derby", "is_knockout", "home", "source"])

    return pd.DataFrame(rows).sort_values("kickoff").reset_index(drop=True)


def fetch_live_recent_form(
    profile: TeamProfile,
    api_token: str,
    limit: int = DEFAULT_RECENT_MATCH_LIMIT,
) -> pd.DataFrame:
    """Fetch recent finished matches from football-data.org as the form context source."""
    team_id = _resolve_team_id(profile)
    if team_id is None:
        raise ValueError("Live form ingestion requires TeamProfile.team_id.")

    payload = _football_data_request(
        f"/teams/{team_id}/matches",
        api_token=api_token,
        params={"status": "FINISHED", "limit": limit},
    )

    rows: list[dict[str, Any]] = []
    for match in payload.get("matches", [])[-limit:]:
        home_team = match.get("homeTeam", {})
        away_team = match.get("awayTeam", {})
        full_time = match.get("score", {}).get("fullTime", {})
        is_home = home_team.get("id") == team_id
        goals_for = full_time.get("home") if is_home else full_time.get("away")
        goals_against = full_time.get("away") if is_home else full_time.get("home")
        if goals_for is None or goals_against is None:
            continue

        if goals_for > goals_against:
            result = "W"
        elif goals_for < goals_against:
            result = "L"
        else:
            result = "D"

        opponent = away_team.get("name") if is_home else home_team.get("name")
        total_goals = goals_for + goals_against
        rows.append(
            {
                "team": profile.team,
                "match": f"vs {opponent}" if is_home else f"at {opponent}",
                "result": result,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "xg_for": round(0.75 + goals_for * 0.55 + (0.15 if is_home else 0), 2),
                "xg_against": round(0.75 + goals_against * 0.55 + (0 if is_home else 0.15), 2),
                "match_total_goals": total_goals,
                "source": "football-data.org",
            }
        )

    if not rows:
        return pd.DataFrame(columns=["team", "match", "result", "goals_for", "goals_against", "xg_for", "xg_against", "match_total_goals", "source"])

    return pd.DataFrame(rows[::-1]).reset_index(drop=True)


def load_upcoming_fixtures(
    profile: TeamProfile | None = None,
    tz: str = DEFAULT_TZ,
    prefer_live: bool = False,
    api_token: str | None = None,
    lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
) -> pd.DataFrame:
    """Load live fixtures when credentials exist, otherwise fall back to sample data."""
    profile = profile or TeamProfile(team="AC Milan")
    token = api_token or os.getenv("FOOTBALL_DATA_API_TOKEN")

    if prefer_live:
        if not token:
            raise ValueError("prefer_live=True requires FOOTBALL_DATA_API_TOKEN or api_token.")
        if _resolve_team_id(profile) is None:
            raise ValueError("prefer_live=True requires TeamProfile.team_id.")

        return fetch_live_upcoming_fixtures(profile=profile, api_token=token, tz=tz, lookahead_days=lookahead_days)

    if token and _resolve_team_id(profile) is not None:
        try:
            return fetch_live_upcoming_fixtures(profile=profile, api_token=token, tz=tz, lookahead_days=lookahead_days)
        except RuntimeError:
            pass

    return sample_upcoming_fixtures(team=profile.team, tz=tz)


def load_recent_form(
    profile: TeamProfile | None = None,
    prefer_live: bool = False,
    api_token: str | None = None,
    limit: int = DEFAULT_RECENT_MATCH_LIMIT,
) -> pd.DataFrame:
    """Load live recent form when available, otherwise keep the local demo sample."""
    profile = profile or TeamProfile(team="AC Milan")
    token = api_token or os.getenv("FOOTBALL_DATA_API_TOKEN")

    if prefer_live:
        if not token:
            raise ValueError("prefer_live=True requires FOOTBALL_DATA_API_TOKEN or api_token.")
        if _resolve_team_id(profile) is None:
            raise ValueError("prefer_live=True requires TeamProfile.team_id.")

        return fetch_live_recent_form(profile=profile, api_token=token, limit=limit)

    if token and _resolve_team_id(profile) is not None:
        try:
            return fetch_live_recent_form(profile=profile, api_token=token, limit=limit)
        except RuntimeError:
            pass

    return sample_recent_form(team=profile.team)


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
