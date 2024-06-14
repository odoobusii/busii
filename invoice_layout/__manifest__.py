# -*- coding: utf-8 -*-
{
    'name': "invoice_layout",

    'summary': """
        Change the invoice layout""",

    'description': """
        Changed the tax nr and spacing of the striped invoice layout
    """,

    'author': "busii",
    'website': "http://www.busii.com",
#/Users/fatimagamieldien/Desktop/odoo-17/odoo-server/addons/invoice_layout/__manifest__.py
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    "version": "17.0",
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        'views/templates.xml',
    ],
}
