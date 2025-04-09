# -*- coding: utf-8 -*-
{
    'name': "Swap Send message and Log note buttons",

    'summary': """
        Swap Send message and Log note buttons""",

    'description': """
        This module swaps Log note and Send message buttons and makes Log note active by default
    """,

    'author': "busii",
    'website': "http://www.busii.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    "version": "18.0.1.0.0",
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,

    # any module necessary for this one to work correctly
    'depends': ['mail'],

    # always loaded
    # 'data': [
    # ],

    'assets': {
   
        'web.assets_backend': [
            'busii_swap_send_message_log_note_btns/static/src/core/chatter/chatter.xml',
        ],
    },
    'images': ['static/description/icon.jpg'],
}
