 # -*- coding: utf-8 -*-
{
    'name': "change_survey_to_aptitude_test",

    'summary': """
        """,

    'description': """
        Change the start survey button to Start Aptitude Test
    """,

    'author': "busii",
    'website': "http://www.busii.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Customizations',
    'version': '17.0.0.0.1',
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': True,

    # any module necessary for this one to work correctly
    'depends': ['base','survey'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        #'views/views.xml',
        'views/templates.xml',
    ],
}
