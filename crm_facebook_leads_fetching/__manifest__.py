{
    'name': "CRM Facebook Lead Ads",
    'summary': """
        Sync Facebook Leads with Odoo CRM""",

    'description': """
    """,
    'author': "M Samiullah",


    'category': 'Lead Automation',
    'version': '1.0',

    'depends': ['crm'],
    'images': ['static/src/img/banner.png'],
    'license': 'AGPL-3',

    'data': [
        # 'data/ir_cron.xml',
        'data/crm.facebook.form.mapping.csv',
        'security/ir.model.access.csv',
 	'security/crm_facebook_leads_security.xml',
        'views/crm_view.xml',
        'views/res_config_settings_views.xml',
    ],
}
