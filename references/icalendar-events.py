#!/usr/bin/env python3
"""No-API calendar reader for morning-brief.

Reads `references/config.json`, fetches `.ics` feeds, parses them with
`icalendar`, and emits JSON for today and the upcoming weekend.
"""
import json
import sys
from datetime import datetime, date, timedelta
from pathlib import Path

from urllib.request import urlopen
from urllib.error import URLError

from icalendar import Calendar

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

MORNING_CONFIG = Path(__file__).resolve().parent.parent / "references" / "config.json"
TZ_TARGET = ZoneInfo("America/Los_Angeles")


def load_config():
    with open(MORNING_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def to_target(dt_val):
    if isinstance(dt_val, datetime):
        if dt_val.tzinfo is None:
            return dt_val.replace(tzinfo=TZ_TARGET)
        return dt_val.astimezone(TZ_TARGET)
    if isinstance(dt_val, date):
        return datetime(dt_val.year, dt_val.month, dt_val.day, tzinfo=TZ_TARGET)
    raise TypeError(f"unsupported dt type {type(dt_val)}")


def parse_ics(text):
    try:
        cal = Calendar.from_ical(text)
    except Exception as e:
        return None, f"parse_failed: {e}"

    now = datetime.now(TZ_TARGET)
    today = now.date()
    # upcoming weekend target: next Saturday through Sunday
    days_to_sat = (5 - today.weekday()) % 7 or 7
    sat = today + timedelta(days=days_to_sat)
    sun = sat + timedelta(days=1)

    window_start = today
    window_end = sun

    events = []
    for component in cal.walk():
        if component.name.upper() != "VEVENT":
            continue

        start_raw = component.get("dtstart")
        end_raw = component.get("dtend")
        if not start_raw:
            continue

        start = to_target(start_raw.dt)
        end = end_raw.dt if end_raw else start + timedelta(hours=1)
        end_dt = to_target(end)
        if end_dt < start:
            end_dt = start + timedelta(hours=1)

        ev_date = start.date()
        if ev_date > window_end or ev_date < window_start:
            continue

        summary = str(component.get("summary", "(no title)"))
        location = str(component.get("location", "") or "")
        description = str(component.get("description", "") or "")
        events.append(
            {
                "summary": summary,
                "start": start.strftime("%Y-%m-%d %H:%M %Z"),
                "end": end_dt.strftime("%Y-%m-%d %H:%M %Z"),
                "location": location,
                "description": description[:180],
            }
        )

    events.sort(key=lambda x: x["start"])
    return events, None


def fetch_ics(url):
    try:
        with urlopen(url, timeout=20) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except URLError as e:
        return None


def main():
    cfg = load_config()
    urls = cfg.get("calendar_urls", []) or []
    if not urls:
        out = {
            "today": datetime.now(TZ_TARGET).strftime("%Y-%m-%d"),
            "upcoming_weekend": [],
            "events": [],
            "errors": ["no calendar_urls configured"],
        }
        print(json.dumps(out, indent=2))
        sys.exit(0)

    all_events = []
    errors = []
    for url in urls:
        text = fetch_ics(url)
        if text is None:
            errors.append(f"fetch failed: {url}")
            continue
        evs, parse_error = parse_ics(text)
        if parse_error:
            errors.append(parse_error)
            continue
        all_events.extend(evs)

    today = datetime.now(TZ_TARGET).date()
    if today.weekday() == 5:      # Saturday
        days_to_sat = 7
    elif today.weekday() == 6:    # Sunday
        days_to_sat = 6
    else:
        days_to_sat = (5 - today.weekday()) % 7
    sat = today + timedelta(days=days_to_sat)
    sun = sat + timedelta(days=1)
    out = {
        "today": today.strftime("%Y-%m-%d"),
        "upcoming_weekend": [sat.strftime("%Y-%m-%d"), sun.strftime("%Y-%m-%d")],
        "events": all_events,
        "errors": errors,
    }
    json.dump(out, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
