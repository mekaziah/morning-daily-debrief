---
name: morning-brief
description: >
  Daily briefing skill: activity, important emails, local news, weather, sky/space views,
  and calendar events for today + upcoming weekend. Prefers free no-API sources; uses
  APIs only when necessary. Composable and evolving — improve section tracks upgrades.
triggers:
  - morning brief
  - daily briefing
  - what is my day looking like
  - daily summary
  - brief me
  - catch me up
  - morning debrief
tools_required:
  - terminal
  - file
  - web_search
  - web_extract
---

# Morning Brief

Single-command daily brief: emails → calendar → weather → news → sky/space → activity.

## Output Format

Return these sections in order:

1. **☀️ Sky** — sunrise/sunset, moon phase/illumination, ISS/satellite passes if available.
2. **📅 Calendar** — today’s events, then upcoming weekend.
3. **📧 Important Emails** — unread or recent important messages since last briefing.
4. **🌤 Weather** — current conditions for configured location.
5. **📰 Local News** — top stories relevant to configured city/region.
6. **📊 Activity** — recent work-in-progress and notable unfinished items, if any.

End with a one-line executive summary.

## Data Sources (prefer no-API, fall back to API only if necessary)

### Sky
- Primary: `ephem` for sunrise/sunset/moon phase calculations.
- Optional: N2YO or similar for ISS pass times if user provides API key in `config.json`.

### Calendar
- Primary: `references/icalendar-events.py` reading `references/config.json` `calendar_urls`.
- Command: `python3 references/icalendar-events.py`
- Output: JSON with `events[]`, plus `today` and `upcoming_weekend`
- Preferred `.ics` sources: `khal` / `icalendar-events-cli`.
- Fallback: Google Calendar only if already authenticated via `google-workspace`; otherwise stay on `.ics`.
- Fallback: `web_extract` on any shared calendar URL.

### Weather
- Primary: `wttr.in` by city or coordinates.
- Fallback: Open-Meteo public endpoint.

### News
- Primary: `web_extract` on local news sites.
- Fallback: `web_search` for "<city> local news today".
- Optional: RSS feeds configured in `references/config.json`.

### Email
- Active bridge: `references/gmail-bridge.py` via stdlib `imaplib.IMAP4_SSL`, reading Himalaya `config.toml` at runtime.
- Command: `python3 references/gmail-bridge.py`
- Output: JSON with `count` + `emails[].from/.subject/.date/.preview`
- Auth: requires App Password; Himalaya stores credentials in `~/.config/himalaya/config.toml`.
- Termux note: strip quoted values from `backend.host` before IMAP login.

### Activity
- Primary: `session_search` for recent unread sessions/work-in-progress since last briefing.
- Secondary: app inventory / Tasker logs if available.
- Fallback: omit if no local source.

## Support Files

- `references/config.json` — user-specific config: location, feeds, thresholds.
- `references/evolution.md` — brief improvement log.
- `references/gmail-bridge.py` — Termux-safe Gmail IMAP helper using stdlib `imaplib`, reads Himalaya config at runtime.
- `references/icalendar-events.py` — no-API calendar reader for `.ics` feeds.

## Evolution Protocol

This skill is designed to improve over time. After each run:

1. Record what worked and what failed in `references/evolution.md`.
2. If a no-API source failed, consider adding a fallback API path for next run.
3. If a source consistently fails, mark it deprecated and find a replacement.
4. Review `references/evolution.md` before each briefing and apply outstanding improvements.
5. Never remove a working no-API source in favor of an API source unless the no-API source is confirmed broken for >30 days.

## Configuration

Store user-specific config in `references/config.json`:
- `location`: city name or "lat,lon"
- `location_latlon`: exact GPS coordinates for local services
- `news_feeds`: list of RSS URLs
- `email_since_hours`: how far back to scan for "important" emails
- `calendar_urls`: list of .ics URLs or local paths
- `iss_api_key`: optional key for satellite passes
- `google_calendar_id`: optional calendar ID for Google Calendar fallback
- `email_limit`: max emails per briefing
- `email_important_subjects`: keywords for filtering

## Scheduled Execution

- Cron job: `morning-brief-daily`
- Schedule: every day at 06:00 PDT
- Delivery: origin chat only

## Termux / Android Notes

- **GPS:** if `location_latlon` is missing, detect via `termux-location` first and update `config.json`.
- **Email:** prefer `references/gmail-bridge.py` over `himalaya` CLI on Termux.
- **Network:** `imaplib.IMAP4_SSL` may need IPv4 restriction on some Termux builds.
- **Moon phases:** use `ephem` when available; if missing, omit rather than failing.
