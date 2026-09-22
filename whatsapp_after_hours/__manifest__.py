# Part of Odoo. Custom module.

{
    'name': "WhatsApp After-Hours Reply",
    'summary': "Sends a free-text session reply to inbound WhatsApp messages received outside office hours, "
               "bypassing template quality-rating exposure.",
    'description': """
WhatsApp After-Hours Reply
===========================
Odoo's WhatsApp module only sends outbound messages through approved templates,
which are subject to Meta's rolling 7-day quality-rating scoring. A one-way
"we're closed" notice tends to get marked as unwanted by recipients, which
degrades and eventually disables the template.

This module sends the after-hours notice as a plain **session (free-text) message**
via the WhatsApp Cloud API instead of a template. Session messages are valid for
any reply sent within the 24-hour customer service window opened by the customer's
own inbound message, and are NOT subject to template quality scoring.

Logic lives here, in a normal installed module, because Automated Action /
Server Action code runs through safe_eval, which blocks the `import requests`
and `import pytz` this needs. The Automated Action itself just calls the method
below.
""",
    'category': 'Customizations',
    'version': '18.0.1.0.0',
    'depends': ['whatsapp', 'base_automation'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_after_hours_log_views.xml',
        # Uncomment the line below to install the Automated Action as data
        # instead of (or in addition to) creating it by hand in the UI.
        'data/whatsapp_after_hours_automation.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    "author": "busii",
    "website": "https://www.busii.com/",
    'images': ['static/description/icon.jpg'],
}
