"""Durable, aggregate-only usage reporting. No prompts or identity data are stored."""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import httpx


def connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=30)
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE IF NOT EXISTS usage_events (
            id INTEGER PRIMARY KEY, occurred_at TEXT NOT NULL,
            model TEXT NOT NULL, outcome TEXT NOT NULL,
            input_tokens INTEGER, output_tokens INTEGER, total_tokens INTEGER
        );
        CREATE INDEX IF NOT EXISTS usage_time ON usage_events(occurred_at);
        CREATE TABLE IF NOT EXISTS report_delivery (
            report_key TEXT PRIMARY KEY, payload TEXT NOT NULL,
            first_attempt REAL NOT NULL, accepted INTEGER NOT NULL DEFAULT 0
        );
    """)
    return db


def record_usage(model: str, usage: dict | None, outcome: str) -> None:
    path = os.getenv("AI_USAGE_DB_PATH", "").strip()
    if not path:
        return
    try:
        values = []
        for name in ("input_tokens", "output_tokens", "total_tokens"):
            value = (usage or {}).get(name)
            values.append(value if type(value) is int and value >= 0 else None)
        if values[2] is None and values[0] is not None and values[1] is not None:
            values[2] = values[0] + values[1]
        with closing(connect(path)) as db, db:
            db.execute("INSERT INTO usage_events VALUES(NULL,?,?,?,?,?,?)", (
                datetime.now(UTC).isoformat(), model, outcome, *values,
            ))
    except Exception:
        # Reporting must not change recipe generation behavior or expose exception data.
        logging.getLogger(__name__).error("usage_record_failed")


def timestamp(value: str) -> str:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Report timestamps must include a timezone.")
    return parsed.astimezone(UTC).isoformat()


def build_report(path: str, start: str, end: str) -> dict:
    start, end = timestamp(start), timestamp(end)
    if start >= end:
        raise ValueError("Report start must precede end.")
    if not Path(path).is_file():
        raise ValueError("Usage database is not initialized; no coverage is available.")
    with closing(connect(path)) as db:
        rows = db.execute("""
            SELECT model, COUNT(*) AS calls,
                SUM(CASE WHEN outcome='failed' THEN 1 ELSE 0 END) AS failures,
                SUM(CASE WHEN input_tokens IS NULL OR output_tokens IS NULL
                    THEN 1 ELSE 0 END) AS calls_missing_usage,
                SUM(input_tokens) AS input_tokens, SUM(output_tokens) AS output_tokens,
                SUM(total_tokens) AS total_tokens
            FROM usage_events WHERE occurred_at >= ? AND occurred_at < ?
            GROUP BY model ORDER BY model
        """, (start, end)).fetchall()
        first_event = db.execute("SELECT MIN(occurred_at) FROM usage_events").fetchone()[0]
    return {
        "period_start_inclusive": start, "period_end_exclusive": end,
        "first_recorded_event": first_event,
        "models": [dict(row) for row in rows],
        "notes": [
            "OpenAI sidecar calls only; provider-reported tokens, not budget estimates.",
            "Coverage starts when recording is enabled; prior usage cannot be reconstructed.",
            "Missing usage is unknown, not zero. Failed calls may still incur provider usage.",
            "SDK-internal retries are not counted separately. Login metrics are not collected.",
        ],
    }


def render_email(report: dict) -> str:
    lines = ["Cookbook usage report", "",
             f"Period: {report['period_start_inclusive']} to {report['period_end_exclusive']}", ""]
    for model in report["models"]:
        lines.append(f"Model: {model['model']}")
        for field, label in (("calls", "Calls"), ("failures", "Failures"),
                             ("input_tokens", "Input tokens"), ("output_tokens", "Output tokens"),
                             ("total_tokens", "Total tokens"), ("calls_missing_usage", "Calls with incomplete token usage")):
            value = model[field]
            lines.append(f"  {label}: {value if value is not None else 'unknown'}")
        lines.append("")
    if not report["models"]:
        lines.append("No recorded calls in this period.")
    lines.extend([f"First recorded event: {report['first_recorded_event'] or 'none'}", "", *report["notes"]])
    return "\n".join(lines)


def send_report(path: str, report: dict, *, transport=None, now: float | None = None) -> str:
    if os.getenv("AI_REPORT_EMAIL_ENABLED", "false").lower() != "true":
        raise ValueError("Report email is disabled.")
    key, sender, recipient = [os.getenv(n, "").strip() for n in (
        "RESEND_API_KEY", "AI_REPORT_FROM", "AI_REPORT_TO",
    )]
    if not all((key, sender, recipient)):
        raise ValueError("Resend key, sender, and recipient must be configured.")
    if any(c in sender + recipient for c in "\r\n"):
        raise ValueError("Invalid email configuration.")
    # Identity includes period and destination, not changing late-arriving metrics.
    identity = json.dumps([report["period_start_inclusive"], report["period_end_exclusive"], sender, recipient])
    report_key = "cookbook-usage/" + hashlib.sha256(identity.encode()).hexdigest()
    payload = json.dumps({
        "from": sender, "to": [recipient],
        "subject": "Cookbook token usage report",
        "text": render_email(report),
    }, sort_keys=True)
    current_time = datetime.now(UTC).timestamp() if now is None else now
    # Serialize sends; persist the exact body before the network call for safe retries.
    with closing(connect(path)) as db:
        db.execute("INSERT OR IGNORE INTO report_delivery VALUES(?,?,?,0)", (report_key, payload, current_time))
        db.commit()
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM report_delivery WHERE report_key=?", (report_key,)).fetchone()
        if row["accepted"]:
            return "already_accepted"
        # Resend retains keys for 24h. Require manual reconciliation after uncertainty.
        if current_time - row["first_attempt"] >= 23 * 3600:
            raise ValueError("Delivery unresolved beyond safe retry window; reconcile with Resend before retrying.")
        try:
            with httpx.Client(transport=transport, timeout=20) as client:
                response = client.post("https://api.resend.com/emails", headers={
                    "Authorization": "Bearer " + key,
                    "Idempotency-Key": report_key,
                    "Content-Type": "application/json",
                }, content=row["payload"])
            if response.status_code != 200 or not response.json().get("id"):
                raise ValueError("Resend did not confirm acceptance.")
        except Exception:
            raise ValueError("Resend acceptance unconfirmed; retry this same report within 23 hours.") from None
        db.execute("UPDATE report_delivery SET accepted=1 WHERE report_key=?", (report_key,))
        db.commit()
    return "accepted"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--send", action="store_true", help="Explicitly send; otherwise preview only")
    args = parser.parse_args()
    try:
        path = os.environ.get("AI_USAGE_DB_PATH", "")
        if not path:
            raise ValueError("AI_USAGE_DB_PATH must be configured.")
        report = build_report(path, args.start, args.end)
        print(send_report(path, report) if args.send else json.dumps(report, indent=2))
    except ValueError as exc:
        parser.exit(1, str(exc) + "\n")


if __name__ == "__main__":
    main()
