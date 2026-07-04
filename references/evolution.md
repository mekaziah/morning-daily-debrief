# Morning Brief Evolution Log

Track successes, failures, and planned upgrades for this skill.

## Format
- Date | Section | Status | Notes | Follow-up

## Entries

- 2026-07-04 | Email | ✅ fixed | Himalaya Rust IMAP crashed on Termux TLS. Replaced with stdlib `imaplib.IMAP4_SSL` bridge reading Himalaya config at runtime. First real INBOX result returned. | Add PDF/calendar attachment detection if needed
- 2026-07-04 | Location | ✅ fixed | `config.json` updated to Vancouver WA via `termux-location` GPS coords. Weather/news now show local results. | None
- 2026-07-03 | Sky | ✅ working | `ephem` installed; sunrise/sunset/moon phase functional. | Add ISS pass source
- 2026-07-03 | Weather | ✅ working | `wttr.in` direct fetch works from Termux. | None
- 2026-07-03 | News | ✅ working | LA/Vancouver local news via direct site extraction. | Add RSS feeds for lower latency
- 2026-07-04 | Calendar | ✅ working | Added no-API Google Calendar via private `.ics` feed. Installed `icalendar`; created `references/icalendar-events.py` primary reader. | None
- 2026-07-04 | Calendar | ✅ improved | Replaced broken or ambiguous Google Calendar API fallback with explicit `.ics` priority and weekday-aware weekend window. | Add recurrence expansion beyond first instance if needed
