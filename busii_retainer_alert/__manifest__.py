{
    'name': 'Customer Retainer Hours Alert',
    'version': '18.0.1.0.1',
    'category': 'Services/Timesheets',
    'summary': 'Monthly retainer hours per customer with an email alert when timesheets reach a set percentage',
    'description': """
Set monthly retainer hours on a customer. Every time a timesheet is logged or
changed on that customer's projects/tasks, the hours for that calendar month
are totalled. When usage reaches the alert threshold (80% by default), one
email per customer per month goes to the users chosen on the customer.
""",
    'author': 'busii',
    'website': 'busii.com',
    'license': 'LGPL-3',
    'depends': ['hr_timesheet'],
    'data': [
        'security/ir.model.access.csv',
        'data/mail_template_data.xml',
        'views/res_partner_views.xml',
        'views/retainer_alert_views.xml',
    ],
    'installable': True,
    'application': False,
}
