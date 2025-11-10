#!/usr/bin/env python3
"""
Send days remaining until a target date (Remedhan) to a Telegram channel.

Usage examples:
    BOT_TOKEN=... CHANNEL_ID=@DaystillRemedhan TARGET_DATE=2026-02-16 python3 post_days_remaining.py
    python3 post_days_remaining.py --token 83733... --channel @DaystillRemedhan --target 2026-02-16

The script supports --dry-run to avoid sending messages while testing.
"""

from __future__ import annotations
import os
import sys
import argparse
from datetime import date, datetime, timedelta
import requests
from typing import Optional

TELEGRAM_SEND_MESSAGE = "https://api.telegram.org/bot{token}/sendMessage"


def days_until(target: date, today: Optional[date] = None) -> int:
    if today is None:
        today = date.today()
    return (target - today).days


def build_progress_bar(percent: int, width: int = 20, fill_char: str = "█", empty_char: str = " ") -> str:
    """Return a zsh-style progress bar like [████      ] based on percent (0-100)."""
    pct = max(0, min(100, percent))
    filled = round(width * pct / 100)
    if filled > width:
        filled = width
    # Use ░ for empty segments as requested
    empty_char = "░"
    return f"[{fill_char * filled}{empty_char * (width - filled)}] {pct}%"


def build_message(
    target: date,
    today: Optional[date] = None,
    *,
    bar_width: int = 20,
    year_days: int = 360,
) -> str:
    if today is None:
        today = date.today()
    d = days_until(target, today)

    # Before start: show days remaining AND percent of days remaining till Remedhan
    if d >= 1:
        percent = int((year_days - d) / year_days * 100)
        bar = build_progress_bar(percent, width=bar_width)
        if d == 1:
            days_msg = "1 day remaining until Remedhan"
        else:
            days_msg = f"{d} days remaining until Remedhan"
        return f"{days_msg} (on {target.isoformat()})\n{bar}"

    elif d == 0:
        return f"Remedhan starts today ({target.isoformat()})."

    # After start: show inline filled progress bar with percent PASSED (not remaining).
    # Keep previous logic for after start
    period_days = 30
    elapsed = (today - target).days
    if elapsed < 0:
        elapsed = 0
    if elapsed > period_days:
        elapsed = period_days
    percent = int((elapsed * 100) // period_days)
    bar = build_progress_bar(percent, width=bar_width)
    if elapsed >= period_days:
        return f"{bar} Remedhan completed (on { (target + timedelta(days=period_days)).isoformat() })."
    else:
        return f"{bar} passed"


def send_telegram_message(token: str, channel: str, text: str, parse_mode: Optional[str] = None) -> dict:
    url = TELEGRAM_SEND_MESSAGE.format(token=token)
    payload = {"chat_id": channel, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    resp = requests.post(url, data=payload, timeout=15)
    try:
        return resp.json()
    except ValueError:
        resp.raise_for_status()


def parse_args(argv) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Post days-until message to a Telegram channel")
    p.add_argument("--token", help="Telegram bot token (or set BOT_TOKEN env var)")
    p.add_argument("--channel", help="Telegram channel id or @username (or set CHANNEL_ID env var)")
    p.add_argument("--target", help="Target date (YYYY-MM-DD) (or set TARGET_DATE env var)")
    p.add_argument("--dry-run", action="store_true", help="Do everything except actually call Telegram API")
    p.add_argument("--bar-width", type=int, default=None, help="Progress bar width (default 20 or BAR_WIDTH env)")
    p.add_argument("--year-days", type=int, default=None, help="Total days in year for percent calculation (default 360)")
    p.add_argument("--today", help=argparse.SUPPRESS)
    return p.parse_args(argv)


def main(argv) -> int:
    args = parse_args(argv)

    token = args.token or os.getenv("BOT_TOKEN")
    channel = args.channel or os.getenv("CHANNEL_ID")
    target_str = args.target or os.getenv("TARGET_DATE")
    bar_width = args.bar_width or int(os.getenv("BAR_WIDTH", "20") or 20)
    year_days = args.year_days or int(os.getenv("YEAR_DAYS", "360") or 360)

    if not token:
        print("Error: bot token is required (pass --token or set BOT_TOKEN).", file=sys.stderr)
        return 2
    if not channel:
        print("Error: channel id is required (pass --channel or set CHANNEL_ID).", file=sys.stderr)
        return 2
    if not target_str:
        print("Error: target date is required (pass --target or set TARGET_DATE).", file=sys.stderr)
        return 2

    # parse target date
    try:
        target_date = datetime.strptime(target_str, "%Y-%m-%d").date()
    except ValueError:
        print("Error: target date must be in YYYY-MM-DD format.", file=sys.stderr)
        return 2

    today = date.today()
    # Allow hidden override for testing
    if args.today:
        try:
            today = datetime.strptime(args.today, "%Y-%m-%d").date()
        except ValueError:
            print("Error: --today must be in YYYY-MM-DD format.", file=sys.stderr)
            return 2

    message = build_message(target_date, today, bar_width=bar_width, year_days=year_days)

    print("Prepared message:")
    print(message)

    if args.dry_run:
        print("Dry run enabled — not sending message.")
        return 0

    print(f"Sending to {channel} using provided bot token...")
    try:
        result = send_telegram_message(token, channel, message)
    except Exception as e:
        print(f"Failed to send message: {e}", file=sys.stderr)
        return 3

    # Telegram returns ok/json
    if isinstance(result, dict) and result.get("ok"):
        print("Message sent successfully.")
        return 0
    else:
        print("Unexpected Telegram response:")
        print(result)
        return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
