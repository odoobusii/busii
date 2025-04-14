# -*- coding: utf-8 -*-
#╔══════════════════════════════════════════════════════════════════════╗
#║                                                                      ║
#║                  ╔═══╦╗       ╔╗  ╔╗     ╔═══╦═══╗                   ║
#║                  ║╔═╗║║       ║║ ╔╝╚╗    ║╔═╗║╔═╗║                   ║
#║                  ║║ ║║║╔╗╔╦╦══╣╚═╬╗╔╬╗ ╔╗║║ ╚╣╚══╗                   ║
#║                  ║╚═╝║║║╚╝╠╣╔╗║╔╗║║║║║ ║║║║ ╔╬══╗║                   ║
#║                  ║╔═╗║╚╣║║║║╚╝║║║║║╚╣╚═╝║║╚═╝║╚═╝║                   ║
#║                  ╚╝ ╚╩═╩╩╩╩╩═╗╠╝╚╝╚═╩═╗╔╝╚═══╩═══╝                   ║
#║                            ╔═╝║     ╔═╝║                             ║
#║                            ╚══╝     ╚══╝                             ║
#║                  SOFTWARE DEVELOPED AND SUPPORTED BY                 ║
#║                ALMIGHTY CONSULTING SOLUTIONS PVT. LTD.               ║
#║                      COPYRIGHT (C) 2016 - TODAY                      ║
#║                      https://www.almightycs.com                      ║
#║                                                                      ║
#╚══════════════════════════════════════════════════════════════════════╝
# Module Was Migrated from Odoo v8: partial code reference taken 
# from v8 gantt view module but structure is rewritten.
{
    "name": "Web Gantt View",
    "version": "18.0.1.0.0",
    "license": "OPL-1",
    "author": "Almighty Consulting Solutions Pvt. Ltd.",
    'website': 'https://www.almightycs.com',
    "category": "Tools",
    'description': """Odoo Web Gantt chart view. gantt view gantt chart project gantt chart""",
    "summary": """Odoo Web Gantt chart view.""",
    'depends': ['web'],
    'data' : [],
    'assets': {
        'web.assets_backend': [
            'web_gantt_view/static/src/css/acs_gantt.css',
            'web_gantt_view/static/lib/dhtmlxGantt/codebase/dhtmlxgantt.css',
            'web_gantt_view/static/lib/dhtmlxGantt/sources/dhtmlxcommon.js',
            'web_gantt_view/static/lib/dhtmlxGantt/sources/dhtmlxgantt.js',
            'web_gantt_view/static/src/js/gantt_model.js',
            'web_gantt_view/static/src/js/gantt_controller.js',
            'web_gantt_view/static/src/js/gantt_renderer.js',
            'web_gantt_view/static/src/js/gantt_view.js',
            'web_gantt_view/static/src/xml/*.xml',
        ],
    },
    'images': [
         'static/description/gantt_view_turkeshpatel_almihgtycs.png',
     ],
    'auto_install': True,
    'installable': True,
    "price": 12,
    "currency": "USD",
}