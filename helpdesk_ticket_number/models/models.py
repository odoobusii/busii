# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# from odoo import api, fields, models
# import re


# class HelpDeskTicketNumber(models.Model):
    
#     _inherit = 'helpdesk.ticket'
    
#     ticket_number = fields.Integer(compute='_compute_ticket_number',store=True)
    
#     @api.depends('name')
#     def _compute_ticket_number(self):
#         regex=re.compile("\(\#([0-9]*)\)")
#         for ticket in self:
#             ticket.ticket_number=int(regex.search(ticket.display_name).group(1))
            
