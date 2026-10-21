from odoo import api, fields, models


class RetainerAlert(models.Model):
    """One record per customer per month once the threshold has been reached.

    The unique constraint is what guarantees the email is only sent once per
    customer per month, even if two people log time at the same moment.
    """
    _name = 'busii.retainer.alert'
    _description = 'Customer Retainer Alert'
    _order = 'period_start desc, id desc'
    _rec_name = 'partner_id'

    partner_id = fields.Many2one('res.partner', string='Customer', required=True, ondelete='cascade', index=True)
    period_start = fields.Date(string='Month', required=True, help='First day of the month the alert applies to.')
    period_label = fields.Char(string='Period', compute='_compute_period_label')
    retainer_hours = fields.Float(string='Retainer Hours', readonly=True)
    hours_used = fields.Float(string='Hours Used at Alert', readonly=True)
    threshold = fields.Float(string='Threshold (%)', readonly=True)
    usage_percent = fields.Float(string='Usage (%)', readonly=True)
    user_ids = fields.Many2many('res.users', string='Notified Users', readonly=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, readonly=True)

    _sql_constraints = [
        ('partner_period_unique', 'unique(partner_id, period_start)',
         'Only one retainer alert per customer per month.'),
    ]

    @api.depends('period_start')
    def _compute_period_label(self):
        for alert in self:
            alert.period_label = alert.period_start.strftime('%B %Y') if alert.period_start else False

    def _send_notification(self):
        template = self.env.ref('busii_retainer_alert.mail_template_retainer_alert', raise_if_not_found=False)
        if not template:
            return
        queued = False
        for alert in self:
            partners = alert.user_ids.partner_id
            if not partners:
                continue
            template.send_mail(
                alert.id,
                force_send=False,  # queued, so a mail server issue never blocks the timesheet save
                email_values={'recipient_ids': [(6, 0, partners.ids)]},
                email_layout_xmlid='mail.mail_notification_light',
            )
            queued = True
        if queued:
            # The Email Queue Manager only runs hourly by default; ask it to run now
            # (in the background, after this transaction commits).
            cron = self.env.ref('mail.ir_cron_mail_scheduler_action', raise_if_not_found=False)
            if cron:
                cron.sudo()._trigger()
