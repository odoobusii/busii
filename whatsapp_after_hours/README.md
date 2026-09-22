# WhatsApp After-Hours Reply

## Why this exists

The original after-hours "we're closed" reply was sent via an approved WhatsApp **template**. Templates are subject to Meta's quality-rating system — a one-way message with no follow-up interaction gets marked "no longer needed" / "spam" by recipients, and Meta downgrades and eventually disables the template over a rolling 7-day window.

This module sends the same message as a **free-text session reply** instead, using the WhatsApp Cloud API directly. Session messages aren't subject to quality scoring — they're valid because the customer's own inbound message opens a 24-hour customer service window, and any reply within that window is allowed as plain text under Meta's own rules.

## How it works

1. A customer messages the business WhatsApp number after hours.
2. An **Automated Action** (Settings → Technical → Automation Rules → "WhatsApp: After-Hours Auto-Reply") fires on creation of the inbound `whatsapp.message` record.
3. It calls `send_after_hours_reply_if_needed()`, which:
   - Checks it's actually inbound and after hours (business hours are configurable — see below)
   - Checks it hasn't already replied to this number recently (de-dup)
   - POSTs a plain-text message straight to `https://graph.facebook.com/v20.0/{phone_number_id}/messages`
   - Logs the send in `whatsapp.after.hours.log` (Settings → Technical → After-Hours Reply Log)
   - Mirrors the reply into the customer's Discuss/WhatsApp chat thread, for agent visibility

## Configuration

All in `models/whatsapp_message.py`, top of the file:

| Constant | Meaning |
|---|---|
| `AFTER_HOURS_MESSAGE` | The reply text |
| `BUSINESS_TZ` | Timezone for the hours check (default `Africa/Johannesburg`) |
| `BUSINESS_START_HOUR` / `BUSINESS_END_HOUR` | Office hours window, Mon–Fri |
| `DEDUP_WINDOW_HOURS` | Don't re-send to the same number within this many hours (default 12) |

## Install

```bash
./odoo-bin -c odoo.conf -d your_db_name -i whatsapp_after_hours --stop-after-init
```

Depends on: `whatsapp`, `base_automation`.

## Known limitations

- **Meta's test/development phone numbers** can only deliver to pre-registered test recipients (Meta for Developers → your app → WhatsApp → API Setup → manage recipient list). A `200` response with a message ID does **not** guarantee delivery outside that list.
- The 24-hour session window is enforced by Meta, not by this module — a customer has to have messaged in recently for a free-text reply to be accepted.
- This bypasses Odoo's own `whatsapp.message._send()`, so the reply won't appear via that path in reports/history — only via the log model and the mirrored channel message.