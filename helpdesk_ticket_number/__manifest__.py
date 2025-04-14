# -*- coding: utf-8 -*-
{
    'name': "Add ticket number",

    'summary': """
    Add ticket number to helpdesk list view
        """,

    'description': """
        Add ticket number to helpdesk list view
    """,

    'author': "Busii",
    'website': "https://www.busii.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    "version": "18.0.1.0.0",
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,

    # any module necessary for this one to work correctly
    'depends': ['base','helpdesk','mail'],

    # always loaded
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    
}
