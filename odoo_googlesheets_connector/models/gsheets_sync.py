from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
import json
from datetime import datetime
import traceback

_logger = logging.getLogger(__name__)


class GSheetsSync(models.Model):
    _name = 'gsheets.sync'
    _description = 'Google Sheets Sync Service'

    def test_connection(self, config):
        """Test connection to Google Sheets"""
        _logger.info(f"[test_connection] Called for config: {config.id}, spreadsheet_id: {config.spreadsheet_id}")
        try:
            credentials = config.get_credentials()
            _logger.info(f"[test_connection] Credentials obtained successfully.")
            # Try to access the spreadsheet
            import gspread
            gc = gspread.authorize(credentials)
            _logger.info(f"[test_connection] gspread authorized.")
            if not config.spreadsheet_id:
                _logger.error('[test_connection] Spreadsheet ID not configured')
                return {'success': False, 'error': 'Spreadsheet ID not configured'}
            spreadsheet = gc.open_by_key(config.spreadsheet_id)
            _logger.info(f"[test_connection] Spreadsheet opened: {spreadsheet}")
            # Try to access the first worksheet
            worksheet = spreadsheet.get_worksheet(0)
            _logger.info(f"[test_connection] Worksheet accessed: {worksheet}")
            return {'success': True, 'message': 'Connection successful'}
        except Exception as e:
            tb = traceback.format_exc()
            _logger.error(f'[test_connection] Exception: {str(e)}\nTraceback:\n{tb}')
            return {'success': False, 'error': str(e)}

    def test_mapping(self, mapping):
        """Test a field mapping configuration"""
        try:
            # Get a sample record
            records = mapping.get_odoo_records()
            if not records:
                return {'success': False, 'error': 'No records found matching the domain'}
            
            # Test field mapping with first record
            sample_record = records[0]
            field_values = mapping.get_field_values(sample_record)
            
            return {
                'success': True, 
                'message': f'Mapping test successful. Sample record has {len(field_values)} fields.'
            }
            
        except Exception as e:
            _logger.error('Mapping test failed: %s', str(e))
            return {'success': False, 'error': str(e)}

    def _notify_failure(self, mapping, error_message, exhausted=False):
        """Post a chatter message to configured partners on failure.
        Uses mapping-level notification settings if configured, otherwise falls back to config settings.
        """
        try:
            # Get effective notification settings
            should_notify = bool(mapping.get_effective_notify_on_failure() or exhausted)
            if not should_notify:
                return
                
            partners = mapping.get_effective_notify_partners()
            partner_ids = partners.ids if partners else []
            
            # Determine which record to post the message to
            target_record = mapping if mapping.use_custom_notification else mapping.config_id
            
            # Get retry counts - use mapping's own retry count if using custom retry, otherwise config's
            if mapping.use_custom_retry:
                attempt = mapping.retry_count
                limit = mapping.get_effective_retry_limit()
            else:
                attempt = mapping.config_id.retry_count
                limit = mapping.config_id.retry_limit
            
            body = _(
                "Google Sheets sync failed for mapping '%(name)s' (Attempt %(attempt)s/%(limit)s).%(final_note)s\nError: %(error)s",
            ) % {
                'name': mapping.name,
                'attempt': attempt,
                'limit': limit,
                'final_note': ' Final attempt exhausted.' if exhausted else '',
                'error': error_message,
            }
            target_record.message_post(body=body, partner_ids=partner_ids)
        except Exception as post_err:
            _logger.warning('Failed to post failure notification for mapping %s: %s', mapping.id, str(post_err))

    def sync_mapping(self, mapping, force=False):
        """Sync data for a specific mapping"""
        mapping.ensure_one()
        
        try:
            # Validate mapping configuration
            mapping.validate_mapping()
            
            # Get configuration
            config = mapping.config_id
            if not config.active or config.state != 'active':
                raise UserError(_('Configuration is not active'))
            
            # Get credentials
            credentials = config.get_credentials()
            
            # Get Odoo records
            records = mapping.get_odoo_records()
            if not records:
                _logger.info('No records to sync for mapping %s', mapping.name)
                # Consider a successful run: reset retries
                if mapping.use_custom_retry:
                    mapping.retry_count = 0
                else:
                    config.retry_count = 0
                return {'success': True, 'records_synced': 0}
            
            # Prepare data for Google Sheets
            data_to_sync = []
            skipped_records = 0
            
            for record in records:
                try:
                    row_data = mapping.get_field_values(record)
                    data_to_sync.append(row_data)
                except Exception as e:
                    if mapping.error_action == 'raise_error':
                        raise
                    else:
                        skipped_records += 1
                        _logger.warning(f'Skipped record {record.id}: {str(e)}')
            
            # Sync to Google Sheets
            import gspread
            gc = gspread.authorize(credentials)
            spreadsheet = gc.open_by_key(config.spreadsheet_id)
            
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(mapping.sheet_name)
            except gspread.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(title=mapping.sheet_name, rows=1000, cols=26)
            
            # Handle headers
            if mapping.include_headers:
                headers = mapping.get_header_values()
                if headers:
                    # Write headers to the specified header row
                    header_range = f'A{mapping.header_row}:{self._get_column_letter(len(headers))}{mapping.header_row}'
                    worksheet.update(range_name=header_range, values=[headers])
            
            # Handle different sync modes
            if mapping.sync_mode == 'replace':
                # Clear existing data (but preserve headers if configured)
                if mapping.include_headers and mapping.header_row > 0:
                    # Clear everything except headers
                    all_values = worksheet.get_all_values()
                    if len(all_values) > mapping.header_row:
                        clear_range = f'A{mapping.header_row + 1}:ZZ{len(all_values)}'
                        worksheet.batch_clear([clear_range])
                else:
                    worksheet.clear()
                
                # Write new data
                if data_to_sync:
                    start_row = mapping.start_row
                    end_row = start_row + len(data_to_sync) - 1
                    end_col = self._get_column_letter(len(data_to_sync[0]))
                    data_range = f'A{start_row}:{end_col}{end_row}'
                    worksheet.update(range_name=data_range, values=data_to_sync)
            
            elif mapping.sync_mode == 'append':
                # Append data to existing content
                if data_to_sync:
                    worksheet.append_rows(data_to_sync)
            
            elif mapping.sync_mode == 'update':
                # Update existing records based on key field
                if not mapping.key_field:
                    raise UserError(_('Key field is required for update mode'))
                
                # Get existing data to find matching records
                existing_data = worksheet.get_all_values()
                header_offset = mapping.header_row if mapping.include_headers else 0
                data_start_row = max(mapping.start_row, header_offset + 1)
                
                if len(existing_data) < data_start_row:
                    # No existing data, just append
                    if data_to_sync:
                        worksheet.append_rows(data_to_sync)
                else:
                    # Find key field column in mapping
                    key_col_index = None
                    for i, field_mapping in enumerate(mapping.field_mapping_ids.sorted('sequence')):
                        if field_mapping.odoo_field == mapping.key_field:
                            key_col_index = i
                            break
                    
                    if key_col_index is None:
                        raise UserError(_('Key field not found in mapping'))
                    
                    # Update or append records
                    updated_count = 0
                    appended_data = []
                    
                    for row_data in data_to_sync:
                        if len(row_data) <= key_col_index:
                            appended_data.append(row_data)
                            continue
                            
                        key_value = str(row_data[key_col_index])
                        found = False
                        
                        # Search in existing data (skip header rows)
                        for row_idx, existing_row in enumerate(existing_data[data_start_row - 1:], data_start_row):
                            if (len(existing_row) > key_col_index and 
                                str(existing_row[key_col_index]) == key_value):
                                # Update existing row
                                end_col = self._get_column_letter(len(row_data))
                                update_range = f'A{row_idx}:{end_col}{row_idx}'
                                worksheet.update(range_name=update_range, values=[row_data])
                                found = True
                                updated_count += 1
                                break
                        
                        if not found:
                            appended_data.append(row_data)
                    
                    # Append new records
                    if appended_data:
                        worksheet.append_rows(appended_data)
                    
                    _logger.info(f'Updated {updated_count} existing records, appended {len(appended_data)} new records')
            
            # Update mapping status on success
            mapping.last_sync = datetime.now()
            mapping.records_synced = len(data_to_sync)
            mapping.state = 'active'
            mapping.error_message = False
            
            # Reset appropriate retry counter
            if mapping.use_custom_retry:
                mapping.retry_count = 0
            else:
                config.retry_count = 0
            
            # Create sync log
            log_message = f'Successfully synced {len(data_to_sync)} records'
            if skipped_records > 0:
                log_message += f', skipped {skipped_records} records due to errors'
                
            self.env['gsheets.sync.log'].create({
                'config_id': config.id,
                'mapping_id': mapping.id,
                'sync_type': 'manual' if force else 'scheduled',
                'records_synced': len(data_to_sync),
                'status': 'success',
                'message': log_message
            })
            
            return {
                'success': True, 
                'records_synced': len(data_to_sync),
                'skipped_records': skipped_records
            }
            
        except Exception as e:
            _logger.error('Sync failed for mapping %s: %s', mapping.name, str(e))
            
            # Increment appropriate retry counter and decide status
            try:
                if mapping.use_custom_retry:
                    mapping.retry_count = (mapping.retry_count or 0) + 1
                    retry_limit = mapping.get_effective_retry_limit()
                    exhausted = mapping.retry_count >= retry_limit
                else:
                    config.retry_count = (config.retry_count or 0) + 1
                    exhausted = config.retry_count >= (config.retry_limit or 0)
            except Exception:
                # Field might not exist on upgraded DB yet; fall back gracefully
                exhausted = False
            
            # Update mapping status
            mapping.error_message = str(e)
            mapping.state = 'error' if exhausted else 'active'
            
            # Create error log
            msg = str(e)
            try:
                if mapping.use_custom_retry:
                    retry_limit = mapping.get_effective_retry_limit()
                    msg = f"{msg} | Retry {mapping.retry_count}/{retry_limit}{' (exhausted)' if exhausted else ''}"
                else:
                    msg = f"{msg} | Retry {config.retry_count}/{config.retry_limit}{' (exhausted)' if exhausted else ''}"
            except Exception:
                # Fallback if fields don't exist yet
                pass
            self.env['gsheets.sync.log'].create({
                'config_id': mapping.config_id.id,
                'mapping_id': mapping.id,
                'sync_type': 'manual' if force else 'scheduled',
                'records_synced': 0,
                'status': 'error',
                'message': msg
            })

            # Notify via chatter if enabled or on exhaustion
            self._notify_failure(mapping, str(e), exhausted=exhausted)
            
            return {'success': False, 'error': str(e), 'exhausted': exhausted}

    def sync_all_active_mappings(self):
        """Sync all active mappings that are due for sync based on their intervals"""
        from datetime import datetime
        
        # Get all active configurations first (not mappings)
        active_configs = self.env['gsheets.config'].search([
            ('active', '=', True),
            ('state', '=', 'active')
        ])
        
        total_synced = 0
        errors = []
        configs_synced = 0
        
        current_time = datetime.now()
        
        for config in active_configs:
            # Check if this config is due for sync
            if not self._is_config_due_for_sync(config, current_time):
                continue
                
            # Get active mappings for this config
            config_mappings = self.env['gsheets.mapping'].search([
                ('active', '=', True),
                ('state', '=', 'active'),
                ('config_id', '=', config.id)
            ])
            
            if not config_mappings:
                # Update next_sync even if no mappings to maintain schedule
                config._schedule_next_sync()
                continue
            
            config_had_errors = False
            config_records_synced = 0
            
            for mapping in config_mappings:
                try:
                    result = self.sync_mapping(mapping)
                    if result.get('success'):
                        config_records_synced += result.get('records_synced', 0)
                    else:
                        config_had_errors = True
                        errors.append(f"{config.name} - {mapping.name}: {result.get('error', 'Unknown error')}")
                except Exception as e:
                    config_had_errors = True
                    errors.append(f"{config.name} - {mapping.name}: {str(e)}")
            
            # Update the configuration's next sync time regardless of individual mapping errors
            # This ensures the configuration doesn't get stuck if some mappings fail
            try:
                config._schedule_next_sync()
                config.last_sync = current_time
                configs_synced += 1
                total_synced += config_records_synced
                
                _logger.info(f'Configuration "{config.name}" sync completed. Records synced: {config_records_synced}, Errors: {config_had_errors}')
            except Exception as e:
                _logger.error(f'Failed to update sync schedule for config "{config.name}": {str(e)}')
        
        _logger.info(f'Cron job completed. Configurations processed: {configs_synced}, Total records synced: {total_synced}, Errors: {len(errors)}')
        
        return {
            'total_synced': total_synced,
            'configs_synced': configs_synced,
            'errors': errors,
            'success': len(errors) == 0
        }
    
    def _is_config_due_for_sync(self, config, current_time):
        """Check if a configuration is due for sync based on its interval and next_sync time"""
        # If no sync interval is set, don't sync
        if not config.sync_interval or config.sync_interval <= 0:
            return False
            
        # If next_sync is not set or is in the past, it's due for sync
        if not config.next_sync:
            _logger.info(f'Configuration "{config.name}" has no next_sync time, marking as due')
            return True
            
        is_due = config.next_sync <= current_time
        if is_due:
            _logger.info(f'Configuration "{config.name}" is due for sync (next_sync: {config.next_sync}, current: {current_time})')
        else:
            _logger.debug(f'Configuration "{config.name}" not due for sync (next_sync: {config.next_sync}, current: {current_time})')
            
        return is_due

    def _get_column_letter(self, column_number):
        """Convert column number to letter (1=A, 2=B, etc.)"""
        result = ""
        while column_number > 0:
            column_number, remainder = divmod(column_number - 1, 26)
            result = chr(65 + remainder) + result
        return result


class GSheetsSyncLog(models.Model):
    _name = 'gsheets.sync.log'
    _description = 'Google Sheets Sync Log'
    _order = 'create_date desc'

    config_id = fields.Many2one('gsheets.config', string='Configuration', required=True)
    mapping_id = fields.Many2one('gsheets.mapping', string='Mapping')
    
    sync_type = fields.Selection([
        ('manual', 'Manual'),
        ('scheduled', 'Scheduled')
    ], string='Sync Type', required=True)
    
    status = fields.Selection([
        ('success', 'Success'),
        ('error', 'Error')
    ], string='Status', required=True)
    
    records_synced = fields.Integer('Records Synced', default=0)
    message = fields.Text('Message')
    
    create_date = fields.Datetime('Created', default=fields.Datetime.now) 