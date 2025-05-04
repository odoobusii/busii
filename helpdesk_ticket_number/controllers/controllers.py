# -*- coding: utf-8 -*-
# from odoo import http


# class HelpdeskTicketNumber423(http.Controller):
#     @http.route('/helpdesk_ticket_number_423/helpdesk_ticket_number_423', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpdesk_ticket_number_423/helpdesk_ticket_number_423/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpdesk_ticket_number_423.listing', {
#             'root': '/helpdesk_ticket_number_423/helpdesk_ticket_number_423',
#             'objects': http.request.env['helpdesk_ticket_number_423.helpdesk_ticket_number_423'].search([]),
#         })

#     @http.route('/helpdesk_ticket_number_423/helpdesk_ticket_number_423/objects/<model("helpdesk_ticket_number_423.helpdesk_ticket_number_423"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpdesk_ticket_number_423.object', {
#             'object': obj
#         })
