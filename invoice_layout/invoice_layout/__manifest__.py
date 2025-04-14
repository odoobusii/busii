# -*- coding: utf-8 -*-
{
    'name': "Enhanced_Striped_Invoice_Layout",
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'author': "busii",
    'website': "http://www.busii.com/odoo-apps",
    'summary': """Change the invoice layout""",
    'description': """
        Changed the tax nr and spacing of the striped invoice layout
    """,
    'support' : "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['base','account'],
    'data': [
        'views/templates.xml',
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
    'auto_install': True,
}
