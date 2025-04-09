# -*- coding: utf-8 -*-
{
    'name': 'BUSII Project portal view update',
    "version": "18.0.1.0.0",
    'license': 'LGPL-3',
    "author": "BUSII",
    "website": "https://www.busii.com/",
    'summary': """busii project portal customization""",
    'description': """
    busii does project planning for external customers and the current portal view does not allow  to share dates and
    other columns when sharing projects. We would therefore like to have additional columns like Order, Blocked by,
    Start_date and End_date fields.
    """,
    'category': "Website",
    'depends': ['website'],
    'data': [
        "views/project_portal_templates.xml",
    ],
    'images': ['static/description/icon.jpg'],
    'installable': True,
    'application': True,
    'auto_install': False,

}