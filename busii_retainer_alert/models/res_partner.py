import logging
import re

from dateutil.relativedelta import relativedelta
from psycopg2 import IntegrityError

from odoo import api, fields, models
from odoo.tools import html2plaintext

_logger = logging.getLogger(__name__)


def _normalise(text):
    """Lower-case, turn punctuation/formatting marks (e.g. *bold*, dashes) and runs of
    whitespace into single spaces, so 'Solution *Investigation*' matches 'solution investigation'."""
    return ' '.join(re.sub(r'[\W_]+', ' ', (text or '').lower()).split())

# Work that is NOT covered by the retainer. Checked in this order; a timesheet
# line is counted once, under the first category it matches.
#   key: (label, text to look for in descriptions, text to look for in tag names)
EXCLUDED_CATEGORIES = [
    ('upskilling', 'Upskilling', 'upskilling', None),
    ('solution_investigation', 'Solution Investigation', 'solution investigation', None),
    ('solution_definition', 'Solution Definition', 'solution definition', None),
    ('development_request', 'Development Requests', None, 'development request'),
]


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
        string='Retainer Hours Used', compute='_compute_retainer_usage', compute_sudo=True,
        help='Hours logged this month that count towards the retainer '
             '(excludes Upskilling, Solution Investigation, Solution Definition and Development Requests).',
    )
    retainer_usage_percent = fields.Float(
        string='Retainer Used (%)', compute='_compute_retainer_usage', compute_sudo=True,
    )
    retainer_hours_total = fields.Float(
        string='Total Hours Logged', compute='_compute_retainer_usage', compute_sudo=True,
        help='All timesheet hours logged this month, including excluded work.',
    )
    retainer_hours_upskilling = fields.Float(
        string='Upskilling', compute='_compute_retainer_usage', compute_sudo=True)
    retainer_hours_solution_investigation = fields.Float(
        string='Solution Investigation', compute='_compute_retainer_usage', compute_sudo=True)
    retainer_hours_solution_definition = fields.Float(
        string='Solution Definition', compute='_compute_retainer_usage', compute_sudo=True)
    retainer_hours_development_request = fields.Float(
        string='Development Requests', compute='_compute_retainer_usage', compute_sudo=True)
    retainer_hours_excluded = fields.Float(
        string='Total Excluded', compute='_compute_retainer_usage', compute_sudo=True)
    retainer_alert_ids = fields.One2many('busii.retainer.alert', 'partner_id', string='Retainer Alerts')

    @api.depends('retainer_hours')
    def _compute_retainer_usage(self):
        period_start = fields.Date.context_today(self).replace(day=1)
        for partner in self:
            breakdown = partner._retainer_breakdown(period_start) if partner.id else {}
            retainer = breakdown.get('retainer', 0.0)
            excluded = sum(breakdown.get(key, 0.0) for key, *_ in EXCLUDED_CATEGORIES)
            partner.retainer_hours_used = retainer
            partner.retainer_hours_total = retainer + excluded
            partner.retainer_hours_excluded = excluded
            partner.retainer_usage_percent = (
                retainer / partner.retainer_hours * 100 if partner.retainer_hours > 0 else 0.0
            )
            for key, *_ in EXCLUDED_CATEGORIES:
                partner[f'retainer_hours_{key}'] = breakdown.get(key, 0.0)

    # ------------------------------------------------------------------
    # Calculation
    # ------------------------------------------------------------------

    def _retainer_period_lines(self, period_start):
        """All timesheet lines for this customer (and its contacts) in the month."""
        self.ensure_one()
        period_end = period_start + relativedelta(months=1)
        return self.env['account.analytic.line'].sudo().search([
            ('project_id', '!=', False),  # timesheets only, not other analytic lines
            ('partner_id.commercial_partner_id', '=', self.commercial_partner_id.id),
            ('date', '>=', period_start),
            ('date', '<', period_end),
        ])

    @api.model
    def _retainer_line_category(self, line, cache):
        """Return the excluded category key for a timesheet line, or 'retainer'."""
        texts = [_normalise(line.name)]
        tag_names = []
        for record in (line.task_id, line._retainer_ticket()):
            if not record:
                continue
            key = (record._name, record.id)
            if key not in cache:
                desc = html2plaintext(record.description or '') if 'description' in record._fields else ''
                tags = record.tag_ids.mapped('name') if 'tag_ids' in record._fields else []
                cache[key] = (_normalise(desc), [_normalise(t) for t in tags])
            desc, tags = cache[key]
            texts.append(desc)
            tag_names += tags
        for key, _label, text, tag in EXCLUDED_CATEGORIES:
            if text and any(text in t for t in texts):
                return key
            if tag and any(tag in name for name in tag_names):
                return key
        return 'retainer'

    def _retainer_breakdown(self, period_start):
        """{'retainer': hours, '<category key>': hours, ...} for the month."""
        self.ensure_one()
        result = {'retainer': 0.0}
        cache = {}
        for line in self._retainer_period_lines(period_start):
            category = self._retainer_line_category(line, cache)
            result[category] = result.get(category, 0.0) + line.unit_amount
        return result

    def _retainer_hours_for_period(self, period_start):
        """Hours that count towards the retainer in the month (excluded work left out)."""
        self.ensure_one()
        return self._retainer_breakdown(period_start)['retainer']

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
