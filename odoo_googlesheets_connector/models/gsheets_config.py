from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json
import base64
import logging
import traceback

_logger = logging.getLogger(__name__)


class GSheetsConfig(models.Model):
    _name = 'gsheets.config'
    _description = 'Google Sheets Configuration'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Configuration Name', required=True)
    active = fields.Boolean('Active', default=True)
    
    # Google API Configuration
    service_account_file = fields.Binary('Service Account JSON File', attachment=True)
    service_account_filename = fields.Char('Service Account Filename')
    
    # Alternative: Manual credentials
    client_id = fields.Char('Client ID')
    client_secret = fields.Char('Client Secret')
    refresh_token = fields.Char('Refresh Token')
    
    # Google Sheets Configuration
    spreadsheet_id = fields.Char('Spreadsheet ID', help='The ID of the Google Spreadsheet')
    spreadsheet_url = fields.Char('Spreadsheet URL', help='Full URL of the Google Spreadsheet')
    
    # Sync Settings
    sync_interval = fields.Integer('Sync Interval (minutes)', default=60)
    last_sync = fields.Datetime('Last Sync')
    next_sync = fields.Datetime('Next Sync')
    
    # Retry & Notification
    retry_limit = fields.Integer('Retry Limit', default=3, help='Number of automatic retry attempts before marking mapping as error')
    retry_count = fields.Integer('Retry Count', default=0, readonly=True, tracking=True)
    notify_on_failure = fields.Boolean('Notify on Failure', default=False)
    notify_partner_ids = fields.Many2many('res.partner', string='Notify Partners')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('configured', 'Configured'),
        ('active', 'Active'),
        ('error', 'Error')
    ], string='Status', default='draft', tracking=True)
    
    error_message = fields.Text('Last Error Message')
    
    # Relationships
    mapping_ids = fields.One2many('gsheets.mapping', 'config_id', string='Field Mappings')
    sync_log_ids = fields.One2many('gsheets.sync.log', 'config_id', string='Sync Logs')

    def _extract_spreadsheet_id_from_url(self, url):
        """Extract spreadsheet ID from Google Sheets URL"""
        if url:
            import re
            pattern = r'/spreadsheets/d/([a-zA-Z0-9-_]+)'
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return False

    @api.onchange('spreadsheet_url')
    def _onchange_spreadsheet_url(self):
        _logger.info(f"[onchange] spreadsheet_url set to: {self.spreadsheet_url}")
        if self.spreadsheet_url:
            extracted_id = self._extract_spreadsheet_id_from_url(self.spreadsheet_url)
            if extracted_id:
                self.spreadsheet_id = extracted_id
                _logger.info(f"[onchange] spreadsheet_id extracted: {self.spreadsheet_id}")
            else:
                _logger.info("[onchange] No spreadsheet_id extracted from url.")

    @api.model
    def create(self, vals):
        """Override create to extract spreadsheet ID from URL"""
        if vals.get('spreadsheet_url') and not vals.get('spreadsheet_id'):
            extracted_id = self._extract_spreadsheet_id_from_url(vals['spreadsheet_url'])
            if extracted_id:
                vals['spreadsheet_id'] = extracted_id
                _logger.info(f"[create] spreadsheet_id extracted and set: {extracted_id}")
        return super(GSheetsConfig, self).create(vals)

    def write(self, vals):
        """Override write to extract spreadsheet ID from URL and auto-schedule sync"""
        if vals.get('spreadsheet_url'):
            extracted_id = self._extract_spreadsheet_id_from_url(vals['spreadsheet_url'])
            if extracted_id:
                vals['spreadsheet_id'] = extracted_id
                _logger.info(f"[write] spreadsheet_id extracted and set: {extracted_id}")
        
        result = super(GSheetsConfig, self).write(vals)
        
        # Auto-schedule next sync when configuration becomes active or sync_interval changes
        for record in self:
            should_schedule = (
                record.state == 'active' and 
                record.sync_interval > 0 and
                (vals.get('state') == 'active' or 
                 'sync_interval' in vals or 
                 not record.next_sync)  # Also schedule if no next_sync is set
            )
            
            if should_schedule:
                record._schedule_next_sync()
                _logger.info(f'Auto-scheduled next sync for configuration "{record.name}" on save')
        
        return result

    @api.constrains('service_account_file', 'client_id', 'client_secret')
    def _check_credentials(self):
        """Ensure at least one authentication method is provided"""
        for record in self:
            if not record.service_account_file and not (record.client_id and record.client_secret):
                raise ValidationError(_('You must provide either a service account file or client credentials.'))

    def action_test_connection(self):
        """Test the Google Sheets connection"""
        self.ensure_one()
        _logger.info(f"[action_test_connection] Called for config: {self.id}, name: {self.name}, spreadsheet_url: {self.spreadsheet_url}, spreadsheet_id: {self.spreadsheet_id}")
        try:
            sync = self.env['gsheets.sync']
            result = sync.test_connection(self)
            _logger.info(f"[action_test_connection] test_connection result: {result}")
            if result.get('success'):
                self.state = 'configured'
                self.error_message = False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Connection to Google Sheets successful!'),
                        'type': 'success',
                    }
                }
            else:
                self.state = 'error'
                self.error_message = result.get('error', 'Unknown error')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Error'),
                        'message': result.get('error', 'Connection failed'),
                        'type': 'danger',
                    }
                }
        except Exception as e:
            tb = traceback.format_exc()
            _logger.error(f"[action_test_connection] Exception: {str(e)}\nTraceback:\n{tb}")
            self.state = 'error'
            self.error_message = str(e)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }

    def action_activate(self):
        """Activate the configuration"""
        self.ensure_one()
        if self.state == 'configured':
            self.state = 'active'
            # Schedule the next sync
            self._schedule_next_sync()
            # Reset retry count when activating
            self.retry_count = 0

    def action_deactivate(self):
        """Deactivate the configuration"""
        self.ensure_one()
        self.state = 'configured'

    def _schedule_next_sync(self):
        """Schedule the next sync based on interval"""
        if self.sync_interval > 0:
            from datetime import datetime, timedelta
            next_sync = datetime.now() + timedelta(minutes=self.sync_interval)
            self.next_sync = next_sync
            _logger.info(f'Configuration "{self.name}" next sync scheduled for: {next_sync} (interval: {self.sync_interval} minutes)')

    def action_manual_sync(self):
        """Manually trigger sync for this configuration (all its mappings)"""
        self.ensure_one()
        
        if self.state != 'active':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Configuration Not Active'),
                    'message': _('Configuration must be active to sync. Current state: %s') % dict(self._fields['state'].selection).get(self.state),
                    'type': 'warning',
                }
            }
        
        # Get active mappings for this config
        config_mappings = self.env['gsheets.mapping'].search([
            ('active', '=', True),
            ('state', '=', 'active'),
            ('config_id', '=', self.id)
        ])
        
        if not config_mappings:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Active Mappings'),
                    'message': _('No active mappings found for this configuration.'),
                    'type': 'info',
                }
            }
        
        try:
            sync_service = self.env['gsheets.sync']
            total_synced = 0
            errors = []
            
            for mapping in config_mappings:
                try:
                    result = sync_service.sync_mapping(mapping, force=True)
                    if result.get('success'):
                        total_synced += result.get('records_synced', 0)
                    else:
                        errors.append(f"{mapping.name}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    errors.append(f"{mapping.name}: {str(e)}")
            
            # Update configuration's last sync time
            from datetime import datetime
            self.last_sync = datetime.now()
            
            # Prepare result message
            if errors:
                message = _('Manual sync completed with errors.\n\nSynced: %s records\nMappings with errors: %s\n\nErrors:\n%s') % (
                    total_synced,
                    len(errors),
                    '\n'.join(errors[:5])  # Limit error list to avoid overwhelming notification
                )
                notification_type = 'warning'
                title = _('Sync Completed with Errors')
            else:
                message = _('Manual sync completed successfully!\n\nSynced: %s records across %s mappings') % (
                    total_synced,
                    len(config_mappings)
                )
                notification_type = 'success'
                title = _('Sync Successful')
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': title,
                    'message': message,
                    'type': notification_type,
                }
            }
            
        except Exception as e:
            _logger.error('Manual sync failed for configuration %s: %s', self.name, str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': _('Manual sync failed: %s') % str(e),
                    'type': 'danger',
                }
            }

    def get_credentials(self):
        """Get Google API credentials"""
        if self.service_account_file:
            # Use service account file
            import tempfile
            import os
            
            # Decode the file content
            file_content = base64.b64decode(self.service_account_file)
            
            # Create a temporary file
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.json', delete=False) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                from google.oauth2 import service_account
                credentials = service_account.Credentials.from_service_account_file(
                    temp_file_path,
                    scopes=[
                        'https://www.googleapis.com/auth/spreadsheets',
                        'https://www.googleapis.com/auth/drive'
                    ]
                )
                return credentials
            finally:
                # Clean up temporary file
                os.unlink(temp_file_path)
        
        elif self.client_id and self.client_secret and self.refresh_token:
            # Use OAuth2 credentials
            from google.oauth2.credentials import Credentials
            
            credentials = Credentials(
                token=None,
                refresh_token=self.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=[
                    'https://www.googleapis.com/auth/spreadsheets',
                    'https://www.googleapis.com/auth/drive'
                ]
            )
            return credentials
        
        else:
            raise ValidationError(_('No valid credentials found. Please configure either service account or OAuth2 credentials.')) 