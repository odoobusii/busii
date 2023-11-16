# -*- coding: utf-8 -*-

from odoo import fields, models, api
from odoo.tools.translate import _


class Task(models.Model):
    _inherit = "project.task"

    acs_date_start = fields.Datetime("Start date")
    acs_date_end = fields.Datetime("End date")

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: