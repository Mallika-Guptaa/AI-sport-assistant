from __future__ import annotations

import os
import smtplib
from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

from src.importance_engine import importance_headline


DEFAULT_TZ = "America/Los_Angeles"


@dataclass
class ReminderPreference:
    remind_day_before: bool = True
    remind_hour_before: bool = True
    only_big_matches: bool = False


@dataclass
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    recipient_email: str
    use_tls: bool = True
    subject_prefix: str = "[AI Sports Assistant]"

    @classmethod
    def from_env(cls) -> "EmailConfig":
        missing = [
            name
            for name in [
                "SMTP_HOST",
                "SMTP_PORT",
                "SMTP_USERNAME",
                "SMTP_PASSWORD",
                "SPORTS_EMAIL_FROM",
                "SPORTS_EMAIL_TO",
            ]
            if not os.getenv(name)
        ]
        if missing:
            raise ValueError(f"Missing email environment variables: {', '.join(missing)}")

        return cls(
            smtp_host=os.environ["SMTP_HOST"],
            smtp_port=int(os.environ["SMTP_PORT"]),
            smtp_username=os.environ["SMTP_USERNAME"],
            smtp_password=os.environ["SMTP_PASSWORD"],
            sender_email=os.environ["SPORTS_EMAIL_FROM"],
            recipient_email=os.environ["SPORTS_EMAIL_TO"],
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            subject_prefix=os.getenv("SPORTS_EMAIL_SUBJECT_PREFIX", "[AI Sports Assistant]"),
        )


def _as_local_timestamp(value: Any, tz: str) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        return ts.tz_localize(ZoneInfo(tz))
    return ts.tz_convert(ZoneInfo(tz))


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
                    "delivery_channel": "email",
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
                    "delivery_channel": "email",
                }
            )

    out = pd.DataFrame(rows)
    if len(out) == 0:
        return out
    return out.sort_values("remind_at").reset_index(drop=True)


def due_reminders(
    reminders_df: pd.DataFrame,
    now: datetime | None = None,
    tz: str = DEFAULT_TZ,
    window_minutes: int = 10,
) -> pd.DataFrame:
    """Return reminders due within a small delivery window."""
    if reminders_df.empty:
        return reminders_df.copy()

    current_time = now or datetime.now(ZoneInfo(tz))
    window_start = current_time - timedelta(minutes=window_minutes)
    due_mask = (reminders_df["remind_at"] <= current_time) & (reminders_df["remind_at"] >= window_start)
    return reminders_df.loc[due_mask].sort_values("remind_at").reset_index(drop=True)


def compose_email(row: pd.Series, config: EmailConfig, tz: str = DEFAULT_TZ) -> EmailMessage:
    kickoff = _as_local_timestamp(row["kickoff"], tz=tz)
    remind_at = _as_local_timestamp(row["remind_at"], tz=tz)

    message = EmailMessage()
    message["From"] = config.sender_email
    message["To"] = config.recipient_email
    message["Subject"] = f"{config.subject_prefix} {row['team']} vs {row['opponent']}"
    message.set_content(
        "\n".join(
            [
                row["message"],
                "",
                f"Competition: {row['competition']}",
                f"Kickoff: {kickoff.strftime('%Y-%m-%d %H:%M %Z')}",
                f"Reminder scheduled for: {remind_at.strftime('%Y-%m-%d %H:%M %Z')}",
            ]
        )
    )
    return message


def send_email_notifications(
    reminders_df: pd.DataFrame,
    config: EmailConfig,
    now: datetime | None = None,
    tz: str = DEFAULT_TZ,
    window_minutes: int = 10,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """
    Send all reminders currently due over SMTP.

    Returns a delivery log so notebooks or scripts can inspect what happened.
    """
    due_df = due_reminders(reminders_df, now=now, tz=tz, window_minutes=window_minutes)
    if due_df.empty:
        return []

    if dry_run:
        return [
            {
                "team": row["team"],
                "opponent": row["opponent"],
                "status": "dry_run",
                "recipient": config.recipient_email,
            }
            for _, row in due_df.iterrows()
        ]

    delivery_log: list[dict[str, Any]] = []
    with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=20) as smtp:
        if config.use_tls:
            smtp.starttls()
        smtp.login(config.smtp_username, config.smtp_password)

        for _, row in due_df.iterrows():
            email = compose_email(row, config=config, tz=tz)
            smtp.send_message(email)
            delivery_log.append(
                {
                    "team": row["team"],
                    "opponent": row["opponent"],
                    "status": "sent",
                    "recipient": config.recipient_email,
                }
            )

    return delivery_log
