import logging

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ResPartner(models.Model):
    _inherit = 'res.partner'

    retainer_hours = fields.Float(
        string='Monthly Retainer Hours',
        help='Hours included in the retainer each calendar month. Leave at 0 to disable alerts.',
    )
    retainer_alert_threshold = fields.Float(
        string='Alert at (%)', default=80.0,
        help='Send the alert email once this percentage of the monthly retainer has been logged.',
    )
    retainer_alert_user_ids = fields.Many2many(
        'res.users', 'res_partner_retainer_alert_user_rel', 'partner_id', 'user_id',
        string='Alert Recipients', domain=[('share', '=', False)],
        help='Internal users who receive the retainer alert email.',
    )
    retainer_hours_used = fields.Float(
        string='Hours Used This Month', compute='_compute_retainer_usage', compute_sudo=True,
    )
    retainer_usage_percent = fields.Float(
        string='Retainer Used (%)', compute='_compute_retainer_usage', compute_sudo=True,
    )
    retainer_alert_ids = fields.One2many('busii.retainer.alert', 'partner_id', string='Retainer Alerts')

    @api.depends('retainer_hours')
    def _compute_retainer_usage(self):
        period_start = fields.Date.context_today(self).replace(day=1)
        for partner in self:
            if partner.retainer_hours > 0 and partner.id:
                used = partner._retainer_hours_for_period(period_start)
                partner.retainer_hours_used = used
                partner.retainer_usage_percent = used / partner.retainer_hours * 100
            else:
                partner.retainer_hours_used = 0.0
                partner.retainer_usage_percent = 0.0

    def _retainer_hours_for_period(self, period_start):
        """Total timesheet hours logged against this customer (and its contacts) in the month."""
        self.ensure_one()
        period_end = period_start + relativedelta(months=1)
        result = self.env['account.analytic.line'].sudo()._read_group(
            [
                ('project_id', '!=', False),  # timesheets only, not other analytic lines
                ('partner_id.commercial_partner_id', '=', self.commercial_partner_id.id),
                ('date', '>=', period_start),
                ('date', '<', period_end),
            ],
            aggregates=['unit_amount:sum'],
        )
        return result[0][0] or 0.0

    def _retainer_check_period(self, period_start):
        """Create the alert and queue the email if the threshold is reached and not yet alerted."""
        self.ensure_one()
        if self.retainer_hours <= 0 or not self.retainer_alert_user_ids:
            return
        Alert = self.env['busii.retainer.alert'].sudo()
        if Alert.search_count([('partner_id', '=', self.id), ('period_start', '=', period_start)]):
            return
        used = self._retainer_hours_for_period(period_start)
        threshold = self.retainer_alert_threshold or 80.0
        if used < self.retainer_hours * threshold / 100.0:
            return
        try:
            with self.env.cr.savepoint():
                alert = Alert.create({
                    'partner_id': self.id,
                    'period_start': period_start,
                    'retainer_hours': self.retainer_hours,
                    'hours_used': used,
                    'threshold': threshold,
                    'usage_percent': used / self.retainer_hours * 100.0,
                    'user_ids': [(6, 0, self.retainer_alert_user_ids.ids)],
                    'company_id': self.env.company.id,
                })
        except IntegrityError:
            # Another transaction created this month's alert at the same moment.
            _logger.info('Retainer alert for partner %s / %s already created concurrently', self.id, period_start)
            return
        alert._send_notification()
