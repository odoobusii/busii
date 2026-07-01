# -*- coding: utf-8 -*-
{
    'name': "Enhanced_Striped_Invoice_Layout",
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',
    'author': "busii",
    'website': "busii.com",
    'summary': """Change the invoice layout""",
    'description': """
        Changed the tax nr and spacing of the striped invoice layout.
        Adjusts the partner address / VAT block, payment term spacing and
        payment reference wording on the standard customer invoice report.
    """,
    'support': "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['base', 'account'],
    'data': [
        'views/templates.xml',
    ],
    'images': ['static/description/after_change.png'],
    'installable': True,
    'application': False,
    'auto_install': True,
}
