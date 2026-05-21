from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Google Sheets Sync Settings
    gsheets_sync_enabled = fields.Boolean('Enable Google Sheets Sync', default=False)
    gsheets_default_config_id = fields.Many2one('gsheets.config', string='Default Configuration')
    gsheets_auto_sync = fields.Boolean('Enable Auto Sync', default=False)
    gsheets_sync_interval = fields.Integer('Default Sync Interval (minutes)', default=60)

    @api.model
    def get_values(self):
        """Get configuration values"""
        res = super(ResConfigSettings, self).get_values()
        config = self.env['ir.config_parameter'].sudo()
        
        res.update(
            gsheets_sync_enabled=config.get_param('gsheets_sync.enabled', default=False),
            gsheets_default_config_id=int(config.get_param('gsheets_sync.default_config_id', default=0)) or False,
            gsheets_auto_sync=config.get_param('gsheets_sync.auto_sync', default=False),
            gsheets_sync_interval=int(config.get_param('gsheets_sync.sync_interval', default=60)),
        )
        return res

    def set_values(self):
        """Set configuration values"""
        super(ResConfigSettings, self).set_values()
        config = self.env['ir.config_parameter'].sudo()
        
        config.set_param('gsheets_sync.enabled', self.gsheets_sync_enabled)
        config.set_param('gsheets_sync.default_config_id', self.gsheets_default_config_id.id or '')
        config.set_param('gsheets_sync.auto_sync', self.gsheets_auto_sync)
        config.set_param('gsheets_sync.sync_interval', self.gsheets_sync_interval) 