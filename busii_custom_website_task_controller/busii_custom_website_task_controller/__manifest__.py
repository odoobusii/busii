# -*- coding: utf-8 -*-
{
    'name': 'Project portal view update',
    'version': '18.0.0.0.1',
    'license': 'LGPL-3',
    "author": "busii",
    "website": "https://www.busii.com/odoo-apps",
    'summary': """busii project portal customization""",
    'description': """
    busii does project planning for external customers and the current portal view does not allow  to share dates and
    other columns when sharing projects. We would therefore like to have additional columns like Order, Blocked by,
    Start_date and End_date fields.
    """,
    'support' : "odooapps@busii.odoo.com",
    'category': 'Customizations',
    'depends': ['project', 'website'],
    'data': [
        "views/project_portal_templates.xml",
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,

}