from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

import pandas as pd

from src.importance_engine import importance_headline


@dataclass
class ReminderPreference:
    remind_day_before: bool = True
    remind_hour_before: bool = True
    only_big_matches: bool = False


def build_reminder_rows(fixtures_df: pd.DataFrame, pref: ReminderPreference) -> pd.DataFrame:
    rows = []

    for _, row in fixtures_df.iterrows():
        if pref.only_big_matches and row["importance_level"] != "high":
            continue

        if pref.remind_day_before:
            rows.append(
                {
                    "team": row["team"],
                    "opponent": row["opponent"],
                    "competition": row["competition"],
                    "kickoff": row["kickoff"],
                    "remind_at": row["kickoff"] - timedelta(days=1),
                    "message": f"1 day reminder: {importance_headline(row)}",
                }
            )

        if pref.remind_hour_before:
            rows.append(
                {
                    "team": row["team"],
                    "opponent": row["opponent"],
                    "competition": row["competition"],
                    "kickoff": row["kickoff"],
                    "remind_at": row["kickoff"] - timedelta(hours=1),
                    "message": f"1 hour reminder: {importance_headline(row)}",
                }
            )

    out = pd.DataFrame(rows)
    if len(out) == 0:
        return out
    return out.sort_values("remind_at").reset_index(drop=True)
