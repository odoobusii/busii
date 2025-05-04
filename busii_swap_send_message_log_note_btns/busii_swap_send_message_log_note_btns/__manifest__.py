# -*- coding: utf-8 -*-
{
    'name': "Swap Send message and Log note buttons",
    "version": "18.0.1.0.0",
    'license': 'LGPL-3',
    'author': "busii",
    'website': "http://www.busii.com/odoo-apps",
    'summary': """Swap Send message and Log note buttons""",
    'description': """
        This module swaps Log note and Send message buttons and makes Log note active by default
    """,
    'support' : "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['mail'],
    'assets': {
        'web.assets_backend': [
            'busii_swap_send_message_log_note_btns/static/src/core/chatter/chatter.xml',
        ],
    },
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
