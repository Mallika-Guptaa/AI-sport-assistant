from __future__ import annotations

import re

import pandas as pd


def answer_query(query: str, scored_fixtures_df: pd.DataFrame) -> str:
    q = query.lower().strip()
    next_match = scored_fixtures_df.sort_values("kickoff").iloc[0]

    if re.search(r"next match|when is .* next", q):
        return (
            f"{next_match['team']}'s next match is vs {next_match['opponent']} in "
            f"{next_match['competition']} at {next_match['kickoff']}."
        )

    if "only for big matches" in q or "big matches" in q:
        high = scored_fixtures_df[scored_fixtures_df["importance_level"] == "high"]
        return (
            f"Done. I will remind only for big matches. "
            f"You currently have {len(high)} high-importance upcoming match(es)."
        )

    if "importance" in q:
        top = scored_fixtures_df.sort_values("importance_score", ascending=False).head(1).iloc[0]
        return (
            f"Most important upcoming match: {top['team']} vs {top['opponent']} "
            f"({top['importance_level']}, score={top['importance_score']})."
        )

    return (
        "I can help with: next match timing, big-match reminders, and match importance. "
        "Try asking: 'When is Milan's next match?'"
    )
