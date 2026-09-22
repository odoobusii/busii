# Part of Odoo. Custom module.

from odoo import fields, models


class WhatsappAfterHoursLog(models.Model):
    """One row per after-hours auto-reply actually sent.

    We call Meta's Graph API directly (bypassing whatsapp.message._send()),
    so nothing in the standard WhatsApp module records that this reply went
    out. We keep our own tiny log, only for de-duplication (so a customer
    who sends 5 messages in one evening only gets the canned reply once)
    and for a quick audit trail.
    """
    _name = 'whatsapp.after.hours.log'
    _description = 'WhatsApp After-Hours Auto-Reply Log'
    _order = 'create_date desc'
    _rec_name = 'mobile_number'

    mobile_number = fields.Char(required=True, index=True, help="Number the auto-reply was sent to (WA-formatted, digits only).")
    wa_account_id = fields.Many2one('whatsapp.account', required=True, ondelete='cascade')
    whatsapp_message_id = fields.Many2one(
        'whatsapp.message', string="Triggering Inbound Message", ondelete='set null',
        help="The inbound whatsapp.message that caused this auto-reply to be sent.")
