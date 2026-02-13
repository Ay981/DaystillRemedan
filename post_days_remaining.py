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
import random
from hijri_converter import Gregorian
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
    # Use ░ for empty segments as requested, no square brackets
    empty_char = "░"
    return f"{fill_char * filled}{empty_char * (width - filled)} {pct}%"


def build_message(
    target: date,
    today: Optional[date] = None,
    *,
    bar_width: int = 20,
    year_days: int = 360,
) -> str:
    # Well-known authentic Ramadan duas (Arabic)
    ramadan_duas = [
        "اللهم بلغنا رمضان وأعنا على صيامه وقيامه وتقبله منا يا أرحم الراحمين",
        "اللهم إنك عفو تحب العفو فاعف عني",
        "اللهم اجعلنا من عتقائك من النار في هذا الشهر الكريم",
        "اللهم تقبل صيامنا وقيامنا وصالح أعمالنا",
        "اللهم ارزقنا ليلة القدر واغفر لنا فيها",
        "اللهم اختم لنا شهر رمضان برضوانك والعتق من نيرانك",
        "اللهم اجعلنا من المقبولين في رمضان",
        "اللهم اغفر لنا وارحمنا وتب علينا إنك أنت التواب الرحيم",
        "اللهم اجعلنا من الذين يستمعون القول فيتبعون أحسنه",
        "اللهم ارزقنا حسن الخاتمة في رمضان وفي كل وقت"
    ]
    if today is None:
        today = date.today()
    # Fix off-by-one: include today in the count (so Shaʻban 25 to Ramadan 1 is 4 days, not 3)
    d = days_until(target, today) + 1

    # Special: post a specific hadith and dua on Shaʻban 25, 1447 AH (2026-02-13)
    special_hadith = "إِذَا دَخَلَ شَهْرُ رَمَضَانَ فُتِّحَتْ أَبْوَابُ السَّمَاءِ وَغُلِّقَتْ أَبْوَابُ جَهَنَّمَ وَسُلْسِلَتْ الشَّيَاطِين‏"
    special_dua = "اللهم بلغنا رمضان وأعنا على صيامه وقيامه وتقبله منا يا أرحم الراحمين"

    # Add Hijri date for today
    hijri = Gregorian(today.year, today.month, today.day).to_hijri()
    hijri_str = f"{hijri.day} {hijri.month_name('ar')} {hijri.year} هـ"

    # Assume Shaʻban ends at 29, so Ramadan starts the next day
    # If target is Ramadan 1, then Shaʻban 29 is target - 1
    # This logic is for pre-Ramadan countdown
    if d >= 1:
        percent = int((year_days - d) / year_days * 100)
        bar = build_progress_bar(percent, width=bar_width)
        if d == 1:
            ar_days = "🕌 يوم واحد متبقٍ (شعبان ٢٩)"
            en_days = "**1 day remaining (Shaʻban 29)**"
        else:
            ar_days = f"🕌 {d} أيام متبقية"
            en_days = f"**{d} days remaining**"
        # Only on Shaʻban 25, 1447 AH (2026-02-13), add the hadith and dua
        if today == date(2026, 2, 13):
            hadith_section = (
                f"\n\n📖 حديث اليوم:\n{special_hadith}\n\n"
                f"🤲 دعاء اليوم:\n{special_dua}\n"
            )
        else:
            hadith_section = ""
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{ar_days}\n"
            f"{en_days}\n\n"
            f"{bar}\n\n"
            f"📅 {hijri_str}\n"
            f"{hadith_section}"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    elif d == 0:
        return (
            f"🌙 رمضان يبدأ اليوم!\nRemedhan starts today!\n"
            f"📅 {hijri_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )

    # After start: show inline filled progress bar with percent PASSED (not remaining).
    # Keep previous logic for after start
    period_days = 29  # Ramadan is 29 days if Shaʻban ends at 29
    elapsed = (today - target).days
    if elapsed < 0:
        elapsed = 0
    if elapsed > period_days:
        elapsed = period_days
    percent = int((elapsed * 100) // period_days)
    bar = build_progress_bar(percent, width=bar_width)
    if elapsed >= period_days:
        return (
            f"✅ رمضان اكتمل!\nRemedhan completed!\n"
            f"{bar}\n"
            f"📅 {hijri_str}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        # Show how many days remain until the end of Ramadan
        days_left = period_days - elapsed
        if days_left == 1:
            days_left_msg = "يوم واحد متبقٍ من رمضان\n1 day remaining of Remedhan"
        else:
            days_left_msg = f"{days_left} أيام متبقية من رمضان\n{days_left} days remaining of Remedhan"
        # Add a random hadith and dua if today is in Ramadan
        in_ramadan = (today >= target) and (today <= target + timedelta(days=period_days-1))
        hadith_section = ""
        if in_ramadan:
            # Only post the hadith if it hasn't been posted yet this Ramadan
            unposted = [h for h in ramadan_hadiths if h not in posted]
            if unposted:
                hadith = unposted[0]
                hadith_section = (
                    f"\n📖 حديث عن رمضان:\n{hadith}"
                    f"\n🤲 دعاء اليوم:\n{random.choice(ramadan_duas)}"
                )
                # Mark as posted
                with open(hadith_file, "a", encoding="utf-8") as f:
                    f.write(hadith + "\n")
            else:
                hadith_section = ""
        return (
            f"{bar} passed\n"
            f"{days_left_msg}\n"
            f"📅 {hijri_str}\n"
            f"{hadith_section}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )


def send_telegram_message(token: str, channel: str, text: str, parse_mode: Optional[str] = None) -> dict:
    url = TELEGRAM_SEND_MESSAGE.format(token=token)
    payload = {"chat_id": channel, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    resp = requests.post(url, data=payload, timeout=15)
    # Try to parse JSON response; if that fails, return status and text to aid debugging
    try:
        j = resp.json()
    except ValueError:
        j = {"ok": False, "http_status": resp.status_code, "http_text": resp.text}
    else:
        # include http status for more context
        if isinstance(j, dict):
            j.setdefault("http_status", resp.status_code)
        else:
            j = {"ok": False, "http_status": resp.status_code, "http_text": str(j)}
    return j


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



    # Post daily until Ramadan starts, then every 3 days during and after Ramadan until next Shaʻban 20
    ramadan_start = target_date
    ramadan_days = 29
    ramadan_end = ramadan_start + timedelta(days=ramadan_days-1)
    # Next Shaʻban 20 (approx, for next year)
    next_shaban_20 = None
    if today >= ramadan_start:
        # Find next Shaʻban 20 (Hijri 20 Shaʻban of next year)
        try:
            from hijri_converter import Hijri
            hijri_today = Gregorian(today.year, today.month, today.day).to_hijri()
            next_year = hijri_today.year + 1 if hijri_today.month > 8 or (hijri_today.month == 8 and hijri_today.day > 20) else hijri_today.year
            next_shaban_20_greg = Hijri(next_year, 8, 20).to_gregorian()
            next_shaban_20 = date(next_shaban_20_greg.year, next_shaban_20_greg.month, next_shaban_20_greg.day)
        except Exception:
            pass

    if today < ramadan_start:
        # Post daily before Ramadan
        pass
    elif today >= ramadan_start and (next_shaban_20 is None or today < next_shaban_20):
        # Post every 3 days during and after Ramadan until next Shaʻban 20
        days_since_ramadan = (today - ramadan_start).days
        if days_since_ramadan % 3 != 0:
            print("Not a posting day (every 3 days during/after Ramadan until next Shaʻban 20). Exiting.")
            return 0
    else:
        # After next Shaʻban 20, stop posting
        print("After next Shaʻban 20, not posting.")
        return 0

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
