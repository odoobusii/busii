# Part of Odoo. Custom module.
#
# This file is a normal installed-module Python file, compiled and imported
# the ordinary way by Odoo -- it is NOT run through safe_eval, so `import
# requests` / `import pytz` below work fine. (Contrast with Automated Action
# / Server Action code, which IS run through safe_eval and blocks both.)

import logging
from datetime import timedelta

import pytz
import requests

from odoo import fields, models

_logger = logging.getLogger(__name__)

# --- Business rules -- adjust these three to match Megan's actual hours/timezone ---
AFTER_HOURS_MESSAGE = "We're currently closed. Thanks for reaching out — we'll call you back tomorrow."
BUSINESS_TZ = 'Africa/Johannesburg'
BUSINESS_START_HOUR = 8   # 08:00 local
BUSINESS_END_HOUR = 17    # 17:00 local, i.e. open [08:00, 17:00)
DEDUP_WINDOW_HOURS = 12   # don't re-send the canned reply to the same number within this window

GRAPH_API_VERSION = 'v20.0'


class WhatsappMessage(models.Model):
    _inherit = 'whatsapp.message'

    def send_after_hours_reply_if_needed(self):
        """Entry point called by the Automated Action on inbound WhatsApp messages.

        Deliberately defensive: every early-exit is a plain `return` (never a
        raise), because this runs inside the same transaction that saves the
        inbound message record coming in off the webhook. An unhandled
        exception here must not roll back that inbound message.
        """
        self.ensure_one()

        if self.message_type != 'inbound':
            return
        if not self.wa_account_id or not self.mobile_number_formatted:
            _logger.warning(
                "After-hours reply skipped: message %s has no account/number.", self.id)
            return
        if not self._after_hours_is_after_hours():
            return
        if self._after_hours_has_recent_reply():
            _logger.info(
                "After-hours reply skipped (already replied to %s within the last %sh).",
                self.mobile_number_formatted, DEDUP_WINDOW_HOURS)
            return

        self._after_hours_send_reply()

    # ------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------

    def _after_hours_is_after_hours(self):
        """True if *now*, in business local time, falls outside office hours."""
        self.ensure_one()
        tz = pytz.timezone(BUSINESS_TZ)
        now_utc = pytz.UTC.localize(fields.Datetime.now())
        now_local = now_utc.astimezone(tz)
        is_weekend = now_local.weekday() >= 5  # 5=Sat, 6=Sun
        is_outside_hours = not (BUSINESS_START_HOUR <= now_local.hour < BUSINESS_END_HOUR)
        return is_weekend or is_outside_hours

    def _after_hours_has_recent_reply(self):
        self.ensure_one()
        cutoff = fields.Datetime.now() - timedelta(hours=DEDUP_WINDOW_HOURS)
        return bool(self.env['whatsapp.after.hours.log'].sudo().search_count([
            ('mobile_number', '=', self.mobile_number_formatted),
            ('wa_account_id', '=', self.wa_account_id.id),
            ('create_date', '>=', cutoff),
        ]))

    def _after_hours_send_reply(self):
        """Call the Graph API directly with a free-text session message.

        This bypasses Odoo's whatsapp.message._send(), which only supports
        template sends. A plain text reply is valid Meta-side because the
        customer's own inbound message opened a 24h customer-service window,
        and session messages (unlike templates) carry no quality rating.
        """
        self.ensure_one()
        account = self.wa_account_id

        # .sudo() matches how Odoo's own WhatsAppApi tool reads this field --
        # `token` is restricted to the whatsapp.group_whatsapp_admin group,
        # and the user context this runs under (webhook/automation) may not
        # be a member of that group.
        access_token = account.sudo().token
        phone_number_id = account.phone_uid
        customer_number = self.mobile_number_formatted

        if not (access_token and phone_number_id and customer_number):
            _logger.error(
                "After-hours reply skipped: missing token/phone_uid/number for message %s.", self.id)
            return

        url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {access_token}"}
        payload = {
            "messaging_product": "whatsapp",
            "to": customer_number,
            "type": "text",
            "text": {"body": AFTER_HOURS_MESSAGE},
        }

        _logger.info(
            "After-hours reply: about to POST %s | to=%s | phone_uid=%s | "
            "raw mobile_number=%s -> mobile_number_formatted=%s | token starts with=%s...",
            url, customer_number, phone_number_id, self.mobile_number,
            self.mobile_number_formatted, (access_token or '')[:8])

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            _logger.info(
                "After-hours reply: Meta responded status=%s body=%s",
                response.status_code, response.text)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # surface Meta's actual error body (e.g. invalid phone_number_id,
            # outside the 24h session window, etc.) instead of just the
            # generic "400 Client Error" text
            _logger.error(
                "After-hours WhatsApp reply to %s failed: %s | response body: %s",
                customer_number, e, response.text)
            return
        except Exception as e:
            _logger.error("After-hours WhatsApp reply to %s failed: %s", customer_number, e)
            return

        # Meta can return HTTP 200 while still reporting a per-message error
        # in the body (e.g. undeliverable, opted out) -- raise_for_status()
        # alone won't catch that, so check the parsed body explicitly too.
        try:
            response_data = response.json()
        except ValueError:
            response_data = {}
        if response_data.get('error') or not response_data.get('messages'):
            _logger.error(
                "After-hours reply to %s: Meta returned HTTP 200 but the body "
                "has no 'messages' entry (or an 'error') -- treating as NOT "
                "delivered. Full body: %s", customer_number, response.text)
            return
        sent_message_id = response_data['messages'][0].get('id')
        _logger.info(
            "After-hours WhatsApp reply sent to %s. Meta message id: %s",
            customer_number, sent_message_id)
        self.env['whatsapp.after.hours.log'].sudo().create({
            'mobile_number': customer_number,
            'wa_account_id': account.id,
            'whatsapp_message_id': self.id,
        })
        self._after_hours_post_in_channel(account, customer_number)

    def _after_hours_post_in_channel(self, account, customer_number):
        """ Best-effort: also post the reply into the customer's active
        Discuss channel, purely for agent visibility in the WhatsApp app.

        This is display only -- it does not go through whatsapp.message._send()
        and does not touch templates or quality ratings. If it fails for any
        reason, that must never affect the fact that the real reply already
        went out via the Graph API call above, so this is wrapped separately
        and never raises.
        """
        try:
            channel = account._find_active_channel(customer_number)
            if not channel:
                return
            channel.sudo().message_post(
                body=AFTER_HOURS_MESSAGE,
                message_type="comment",
                subtype_xmlid='mail.mt_comment',
            )
        except Exception as e:
            _logger.warning(
                "After-hours reply sent to %s but could not be mirrored into "
                "the Discuss channel for visibility: %s", customer_number, e)
