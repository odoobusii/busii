# -*- coding: utf-8 -*-
# from odoo import http


# class 495InvoiceLayout(http.Controller):
#     @http.route('/495_invoice_layout/495_invoice_layout', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/495_invoice_layout/495_invoice_layout/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('495_invoice_layout.listing', {
#             'root': '/495_invoice_layout/495_invoice_layout',
#             'objects': http.request.env['495_invoice_layout.495_invoice_layout'].search([]),
#         })

#     @http.route('/495_invoice_layout/495_invoice_layout/objects/<model("495_invoice_layout.495_invoice_layout"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('495_invoice_layout.object', {
#             'object': obj
#         })
