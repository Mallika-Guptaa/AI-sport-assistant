from __future__ import annotations

import pandas as pd


def score_match_importance(
    fixtures_df: pd.DataFrame,
    current_rank: int = 4,
    target_rank: int = 4,
    streak: int = 0,
) -> pd.DataFrame:
    """Rule-based importance score designed as an interpretable AI baseline."""
    df = fixtures_df.copy()

    score = (
        df["is_derby"] * 35
        + df["is_knockout"] * 30
        + (df["competition"].eq("Champions League") * 25)
        + (df["opponent"].isin(["Inter Milan", "Juventus", "Napoli", "PSG"]) * 15)
    )

    # Must-win pressure if team is at/near target boundary (e.g., top 4)
    pressure = 10 if current_rank >= target_rank else 4
    score = score + pressure

    # Momentum amplifies perceived importance
    if streak >= 3:
        score = score + 8
    elif streak <= -2:
        score = score + 12

    df["importance_score"] = score.clip(0, 100)
    df["importance_level"] = pd.cut(
        df["importance_score"],
        bins=[-1, 39, 69, 100],
        labels=["low", "medium", "high"],
    )
    return df


def importance_headline(row: pd.Series) -> str:
    if row["importance_level"] == "high":
        return f"Big match today 🔥 ({row['team']} vs {row['opponent']})"
    if row["importance_level"] == "medium":
        return f"Important fixture tonight: {row['team']} vs {row['opponent']}"
    return f"Upcoming match: {row['team']} vs {row['opponent']}"


def context_insight(team: str, streak: int, current_rank: int, target_rank: int) -> str:
    if streak >= 3:
        streak_text = f"{team} is on a {streak}-match winning streak ⚡"
    elif streak <= -2:
        streak_text = f"{team} is on a {abs(streak)}-match losing run and needs a response"
    else:
        streak_text = f"{team}'s recent form is mixed"

    if current_rank >= target_rank:
        rank_text = f"Must-win game to stay in top {target_rank}"
    else:
        rank_text = f"Chance to strengthen top {target_rank} position"

    return f"{streak_text}. {rank_text}."
