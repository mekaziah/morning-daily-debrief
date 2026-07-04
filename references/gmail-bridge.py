#!/usr/bin/env python3
"""
Email helper for morning-brief.
Reads Himalaya Gmail config at runtime, then fetches recent unread/important emails via stdlib imaplib only.
No external mail packages required. No secrets persisted.
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
import configparser
import imaplib
import email
from email.header import decode_header
import ssl

HIMALAYA_CONFIG = Path.home() / ".config" / "himalaya" / "config.toml"
MORNING_CONFIG = Path(__file__).resolve().parent.parent / "references" / "config.json"


def read_himalaya_gmail():
    cp = configparser.ConfigParser()
    cp.read(HIMALAYA_CONFIG)
    section = "accounts.gmail"
    email = cp.get(section, "email", fallback="")
    password = cp.get(section, "backend.auth.raw", fallback="")
    host = (cp.get(section, "backend.host", fallback="imap.gmail.com") or "").strip("\"'")
    port_raw = cp.get(section, "backend.port", fallback="993").strip("\"'")
    try:
        port = int(port_raw)
    except ValueError:
        port = 993
    return {
        "email": email,
        "password": password,
        "host": host or "imap.gmail.com",
        "port": port,
    }


def load_morning_config():
    with open(MORNING_CONFIG, "r") as f:
        return json.load(f)


def important_keywords():
    cfg = load_morning_config()
    kws = cfg.get("important_keywords", "urgent,important,action,required,deadline,asap")
    if isinstance(kws, str):
        return [w.strip().lower() for w in kws.split(",") if w.strip()]
    return [w.strip().lower() for w in kws]


def decode_mime_words(raw):
    if not raw:
        return ""
    parts = decode_header(raw)
    out = []
    for part, charset in parts:
        if isinstance(part, bytes):
            out.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            out.append(part)
    return " ".join(out)


def body_text(msg):
    text = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            if ct == "text/plain":
                try:
                    body = part.get_payload(decode=True)
                    charset = part.get_content_charset() or "utf-8"
                    text = (body or b"").decode(charset, errors="replace")
                    if text:
                        break
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True)
            charset = msg.get_content_charset() or "utf-8"
            text = (body or b"").decode(charset, errors="replace")
        except Exception:
            pass
    return text.replace("\n", " ")


def main():
    gmail = read_himalaya_gmail()
    if not gmail.get("email") or not gmail.get("password"):
        print("CONFIG ERROR: gmail account missing or incomplete in Himalaya config.toml", file=sys.stderr)
        sys.exit(2)

    cfg = load_morning_config()
    since_hours = int(cfg.get("email_since_hours", 12))
    limit = int(cfg.get("email_limit", 20))
    since_dt = datetime.now() - timedelta(hours=since_hours)
    since_str = since_dt.strftime("%d-%b-%Y")

    kws = important_keywords()

    out = []
    conn = None
    try:
        ctx = ssl.create_default_context()
        # preferred cert bundle; falls back if missing
        cert_path = Path("/data/data/com.termux/files/usr/etc/tls/cert.pem")
        if cert_path.exists():
            ctx.load_verify_locations(str(cert_path))
        conn = imaplib.IMAP4_SSL(host=gmail["host"], port=gmail["port"], ssl_context=ctx)
        conn.login(gmail["email"], gmail["password"])
        conn.select("INBOX")

        # Use MULTIAPPEND-capable search string with date and unread
        typ, data = conn.search(None, f"(UNSEEN SINCE {since_str})")
        if typ != "OK":
            raise RuntimeError(f"IMAP SEARCH failed: {typ}")
        ids = (data[0] or b"").split()[:limit]
        for num in ids:
            typ2, msg_data = conn.fetch(num, "(BODY.PEEK[])")
            if typ2 != "OK":
                continue
            raw = msg_data[0][1]
            msg = email.message_from_bytes(raw)
            subject = decode_mime_words(msg.get("Subject", ""))
            frm = decode_mime_words(msg.get("From", ""))
            preview = body_text(msg)[:220]
            blob = f"{subject} {frm} {preview}".lower()
            if any(k in blob for k in kws):
                out.append(
                    {
                        "from": frm,
                        "subject": subject,
                        "date": msg.get("Date", ""),
                        "preview": preview,
                    }
                )
    except Exception as e:
        print(f"IMAP ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            try:
                conn.close()
                conn.logout()
            except Exception:
                pass

    json.dump({"count": len(out), "emails": out}, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
