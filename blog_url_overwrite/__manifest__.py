# -*- coding: utf-8 -*-
{
    'name': 'Overwrite BlogPost URL',
    'version': '18.0.0.1',
    'license': 'LGPL-3',
    "author": "busii",
    "website": "https://www.busii.com/odoo-apps",
    'summary': """Customise Blog post urls.""",
    'description': """
        Customise Blog post urls.
        """,
    'support' : "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['base', 'website', 'website_blog'],
    'data': [
        'views/post_loop_override.xml',

    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
