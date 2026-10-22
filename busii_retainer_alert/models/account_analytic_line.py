from odoo import api, models

# Changes to these fields can move hours into or out of a customer's month,
# or into or out of an excluded category.
RETAINER_TRIGGER_FIELDS = {'unit_amount', 'date', 'project_id', 'task_id', 'partner_id', 'name', 'helpdesk_ticket_id'}


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        lines._retainer_check_alerts()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if RETAINER_TRIGGER_FIELDS & set(vals):
            self._retainer_check_alerts()
        return res

    def _retainer_ticket(self):
        """The helpdesk ticket of the line, if Helpdesk Timesheet is installed."""
        self.ensure_one()
        if 'helpdesk_ticket_id' in self._fields:
            return self.helpdesk_ticket_id
        return self.env['res.partner']  # empty recordset; skipped by the caller

    def _retainer_check_alerts(self):
        to_check = set()
        for line in self.sudo().filtered('project_id'):
            partner = line.partner_id.commercial_partner_id
            if partner and partner.retainer_hours > 0 and line.date:
                to_check.add((partner, line.date.replace(day=1)))
        for partner, period_start in to_check:
            partner._retainer_check_period(period_start)
