# models/account_analytic_line.py
from odoo import models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'

    def _show_portal_timesheets(self):
        """Show timesheet data only to internal users; hide from portal/public users."""
        return not self.env.user.share
    