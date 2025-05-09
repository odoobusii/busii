# -*- coding: utf-8 -*-
{
    'name': "Custom Partner Ledger Report",
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    'author': "busii",
    'website': "http://www.busii.com/odoo-apps",
    'summary': """Change the Partner Ledger layout""",
    'description': """
        Customised the Partner Ledger report layout and changed heading from 'PARTNER LEDGER' to 'CUSTOMER STATEMENT'.
    """,
    'support' : "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['account_reports'],
    'data': [
        'views/templates.xml',
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
    'auto_install': True,
}
