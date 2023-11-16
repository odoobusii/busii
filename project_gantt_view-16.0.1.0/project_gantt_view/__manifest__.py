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
{
    "name": "Project Gantt View",
    "version": "1.0",
    "license": "OPL-1",
    "author": "Almighty Consulting Solutions Pvt. Ltd.",
    'website': 'https://www.almightycs.com',
    "category": "Project",
    "description": """Odoo Project Web Gantt chart view.""",
    "summary": """Odoo Project Web Gantt chart view.""",
    "depends": ['web_gantt_view','project'],
    "data" : [
        'views/project_view.xml', 
    ],
    'images': [
        'static/description/acs_gantt_view_groupby_odoo_almightycs.png',
    ],
    'installable': True,
    'application': True,
    'sequence': 1,
    'price': 2,
    'currency': 'USD',
}
