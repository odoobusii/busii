# -*- coding: utf-8 -*-

from odoo import models, fields, api


class invoice_layout(models.Model):
    _inherit = 'account.move'
    _description = 'invoice'
