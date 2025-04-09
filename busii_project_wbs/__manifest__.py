# -*- coding: utf-8 -*-
{
    'name': "WBS Project View",

    'summary': """
        Adds a wbs view in projects""",

    'description': """
        Adds a wbs view in projects
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

    # any module necessary for this one to work correctly
    'depends': ['project', 'web_gantt'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/assets.xml',
        'views/project_project_views.xml',
        'views/project_task_gantt_view.xml',
    ],
   
    'images': ['static/description/icon.png'],
}
