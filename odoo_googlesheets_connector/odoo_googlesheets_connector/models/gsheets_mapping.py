from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class GSheetsMapping(models.Model):
    _name = 'gsheets.mapping'
    _description = 'Google Sheets Field Mapping'
    _order = 'sequence, id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Mapping Name', required=True)
    config_id = fields.Many2one('gsheets.config', string='Configuration', required=True, ondelete='cascade')
    active = fields.Boolean('Active', default=True)
    sequence = fields.Integer('Sequence', default=10)
    
    # Odoo Model Configuration
    model_id = fields.Many2one('ir.model', string='Odoo Model', required=True, ondelete='cascade')
    model_name = fields.Char(related='model_id.model', readonly=True)
    filter_domain = fields.Char(string="Filter Domain", help='Odoo domain to filter records')
    limit = fields.Integer('Record Limit', default=1000, help='Maximum number of records to sync')
    
    # Advanced Filtering
    use_date_filter = fields.Boolean('Use Date Range Filter', default=False)
    date_field = fields.Many2one('ir.model.fields', string='Date Field', 
                                domain="[('model_id', '=', model_id), ('ttype', 'in', ['date', 'datetime'])]")
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    
    # Google Sheets Configuration
    sheet_name = fields.Char('Sheet Name', required=True, help='Name of the worksheet in Google Sheets')
    start_row = fields.Integer('Start Row', default=2, help='Row number to start writing data (1-based)')
    start_col = fields.Integer('Start Column', default=1, help='Column number to start writing data (1-based)')
    
    # Header Management
    include_headers = fields.Boolean('Include Headers', default=True)
    header_row = fields.Integer('Header Row', default=1, help='Row number for headers (1-based)')
    custom_headers = fields.Boolean('Use Custom Headers', default=False)
    
    # Field Mappings
    field_mapping_ids = fields.One2many('gsheets.field.mapping', 'mapping_id', string='Field Mappings')
    
    # Sync Settings
    sync_mode = fields.Selection([
        ('append', 'Append'),
        ('replace', 'Replace All'),
        ('update', 'Update Existing')
    ], string='Sync Mode', default='append', required=True)
    
    key_field = fields.Many2one('ir.model.fields', string='Key Field', 
                               domain="[('model_id', '=', model_id)]",
                               help='Field to use as unique identifier for updates')
    
    # Error Handling
    skip_errors = fields.Boolean('Skip Records with Errors', default=True)
    error_action = fields.Selection([
        ('skip', 'Skip Record'),
        ('use_default', 'Use Default Value'),
        ('raise_error', 'Raise Error')
    ], string='Error Action', default='skip')

    # Retry & Notification (Override config defaults)
    use_custom_retry = fields.Boolean('Use Custom Retry Settings', default=False)
    retry_limit = fields.Integer('Retry Limit', help='Number of automatic retry attempts before marking mapping as error. Leave 0 to use configuration default.')
    retry_count = fields.Integer('Retry Count', default=0, readonly=True, tracking=True)
    
    use_custom_notification = fields.Boolean('Use Custom Notification Settings', default=False)
    notify_on_failure = fields.Boolean('Notify on Failure', help='Enable notifications for this mapping. Uses configuration default if custom settings disabled.')
    notify_partner_ids = fields.Many2many('res.partner', string='Notify Partners', help='Partners to notify for this mapping. Uses configuration partners if custom settings disabled.')

    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('error', 'Error')
    ], string='Status', default='draft', tracking=True)
    
    last_sync = fields.Datetime('Last Sync')
    records_synced = fields.Integer('Records Synced', default=0)
    error_message = fields.Text('Last Error Message')

    model_name = fields.Char(string="Model Name", compute="_compute_model_name", store=True)

    @api.constrains('model_id', 'key_field')
    def _check_key_field(self):
        """Ensure key field belongs to the selected model"""
        for record in self:
            if record.key_field and record.key_field.model_id != record.model_id:
                raise ValidationError(_('Key field must belong to the selected model.'))

    @api.onchange('model_id')
    def _onchange_model_id(self):
        """Reset key field when model changes"""
        self.key_field = False

    @api.depends('model_id')
    def _compute_model_name(self):
        for rec in self:
            rec.model_name = rec.model_id.model or False

    def get_effective_retry_limit(self):
        """Get the effective retry limit (mapping override or config default)"""
        self.ensure_one()
        if self.use_custom_retry and self.retry_limit > 0:
            return self.retry_limit
        return self.config_id.retry_limit or 3

    def get_effective_notify_on_failure(self):
        """Get the effective notify on failure setting (mapping override or config default)"""
        self.ensure_one()
        if self.use_custom_notification:
            return self.notify_on_failure
        return self.config_id.notify_on_failure

    def get_effective_notify_partners(self):
        """Get the effective notification partners (mapping override or config default)"""
        self.ensure_one()
        if self.use_custom_notification and self.notify_partner_ids:
            return self.notify_partner_ids
        return self.config_id.notify_partner_ids

    def action_test_mapping(self):
        """Test the field mapping configuration"""
        self.ensure_one()
        try:
            sync = self.env['gsheets.sync']
            result = sync.test_mapping(self)
            
            if result.get('success'):
                self.state = 'active'
                self.error_message = False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Success'),
                        'message': _('Mapping test successful!'),
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
                        'message': result.get('error', 'Mapping test failed'),
                        'type': 'danger',
                    }
                }
        except Exception as e:
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

    def action_apply_template(self):
        """Action to apply a predefined template"""
        self.ensure_one()
        
        # Apply Sales Orders template directly for now
        # This can be enhanced later with template selection
        try:
            self.apply_template_data('sales_orders')
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Template Applied'),
                    'message': _('Sales Orders template applied successfully! The mapping now includes Order Number, Customer, Date, Amount, and Status fields. Review and test when ready.'),
                    'type': 'success',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Template Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    def action_manual_sync(self):
        """Manually trigger sync for just this mapping"""
        self.ensure_one()
        
        if self.state != 'active':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Mapping Not Active'),
                    'message': _('Mapping must be active to sync. Current state: %s') % dict(self._fields['state'].selection).get(self.state),
                    'type': 'warning',
                }
            }
        
        if self.config_id.state != 'active':
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Configuration Not Active'),
                    'message': _('The Google Sheets configuration "%s" must be active to sync.') % self.config_id.name,
                    'type': 'warning',
                }
            }
        
        try:
            sync_service = self.env['gsheets.sync']
            result = sync_service.sync_mapping(self, force=True)
            
            if result.get('success'):
                message = _('Manual sync completed successfully!\n\nRecords synced: %s') % result.get('records_synced', 0)
                if result.get('skipped_records', 0) > 0:
                    message += _('\nSkipped records: %s') % result.get('skipped_records')
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sync Successful'),
                        'message': message,
                        'type': 'success',
                    }
                }
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Sync Failed'),
                        'message': _('Manual sync failed: %s') % result.get('error', 'Unknown error'),
                        'type': 'danger',
                    }
                }
        
        except Exception as e:
            _logger.error('Manual sync failed for mapping %s: %s', self.name, str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Sync Failed'),
                    'message': _('Manual sync failed: %s') % str(e),
                    'type': 'danger',
                }
            }

    def get_odoo_records(self):
        """Get Odoo records based on mapping configuration"""
        self.ensure_one()
        
        # Build domain
        domain = []
        if self.filter_domain:
            try:
                domain = eval(self.filter_domain)
            except Exception as e:
                raise ValidationError(_('Invalid domain: %s') % str(e))
        
        # Add date range filter if configured
        if self.use_date_filter and self.date_field:
            if self.date_from:
                domain.append((self.date_field.name, '>=', self.date_from))
            if self.date_to:
                domain.append((self.date_field.name, '<=', self.date_to))
        
        # Get records
        model = self.env[self.model_id.model]
        records = model.search(domain, limit=self.limit)
        
        return records
    
    def get_field_values(self, record):
        """Get field values for a record based on enhanced mapping"""
        self.ensure_one()
        values = []
        
        for field_mapping in self.field_mapping_ids.sorted('sequence'):
            try:
                # Use the new enhanced formatting method
                formatted_value = field_mapping.get_formatted_value(record)
                values.append(formatted_value)
            except Exception as e:
                if self.error_action == 'raise_error':
                    raise
                elif self.error_action == 'use_default':
                    values.append(field_mapping.default_value or '')
                else:  # skip
                    values.append(f'Error: {str(e)}')
        
        return values
    
    def get_header_values(self):
        """Get header values for the mapping"""
        self.ensure_one()
        headers = []
        
        for field_mapping in self.field_mapping_ids.sorted('sequence'):
            if self.custom_headers and field_mapping.custom_header:
                headers.append(field_mapping.custom_header)
            elif field_mapping.odoo_field:
                headers.append(field_mapping.odoo_field.field_description or field_mapping.odoo_field.name)
            else:
                headers.append(field_mapping.gsheets_column)
        
        return headers
    
    def validate_mapping(self):
        """Validate the mapping configuration"""
        self.ensure_one()
        errors = []
        
        # Check if field mappings exist
        if not self.field_mapping_ids:
            errors.append(_("No field mappings configured"))
        
        # Validate each field mapping
        for field_mapping in self.field_mapping_ids:
            try:
                # Validate expressions
                if field_mapping.mapping_type in ['expression', 'computed'] and field_mapping.custom_expression:
                    # Test with a dummy record
                    test_record = self.env[self.model_id.model].search([], limit=1)
                    if test_record:
                        field_mapping._evaluate_expression(test_record, field_mapping.custom_expression)
                
                # Validate condition expressions
                if field_mapping.use_condition and field_mapping.condition_expression:
                    test_record = self.env[self.model_id.model].search([], limit=1)
                    if test_record:
                        field_mapping._evaluate_expression(test_record, field_mapping.condition_expression)
                        
            except Exception as e:
                errors.append(_("Field mapping '{}': {}").format(field_mapping.gsheets_column, str(e)))
        
        # Validate date filter configuration
        if self.use_date_filter and not self.date_field:
            errors.append(_("Date field is required when using date range filter"))
        
        if errors:
            raise ValidationError('\n'.join(errors))
        
        return True
    
    def get_data_preview(self, limit=5):
        """Get a preview of the data that would be synced"""
        self.ensure_one()
        try:
            records = self.get_odoo_records()
            if not records:
                return {'headers': [], 'rows': [], 'message': 'No records found'}
            
            # Limit records for preview
            preview_records = records[:limit]
            
            # Get headers
            headers = self.get_header_values() if self.include_headers else []
            
            # Get data rows
            rows = []
            for record in preview_records:
                row_data = self.get_field_values(record)
                rows.append(row_data)
            
            return {
                'headers': headers,
                'rows': rows,
                'total_records': len(records),
                'preview_count': len(preview_records)
            }
        except Exception as e:
            return {'error': str(e)}
    
    def action_preview_data(self):
        """Action to preview data before syncing"""
        self.ensure_one()
        try:
            preview = self.get_data_preview()
            if 'error' in preview:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Preview Error'),
                        'message': preview['error'],
                        'type': 'danger',
                    }
                }
            
            # Create a simple preview message
            message = f"Preview:\n"
            message += f"Total Records: {preview.get('total_records', 0)}\n"
            message += f"Preview Count: {preview.get('preview_count', 0)}\n\n"
            
            if preview.get('headers'):
                message += f"Headers: {', '.join(preview['headers'])}\n\n"
            
            if preview.get('rows'):
                message += "Sample Data:\n"
                for i, row in enumerate(preview['rows'][:3], 1):
                    message += f"Row {i}: {', '.join(str(cell)[:30] + '...' if len(str(cell)) > 30 else str(cell) for cell in row)}\n"
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Data Preview'),
                    'message': message,
                    'type': 'info',
                }
            }
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Error'),
                    'message': str(e),
                    'type': 'danger',
                }
            }
    
    def apply_template_data(self, template_key):
        """Apply template data to current mapping"""
        self.ensure_one()
        
        templates = {
            'sales_orders': {
                'model': 'sale.order',
                'fields': [
                    {'name': 'name', 'type': 'text', 'header': 'Order Number'},
                    {'name': 'partner_id', 'type': 'text', 'header': 'Customer'},
                    {'name': 'date_order', 'type': 'date', 'header': 'Order Date'},
                    {'name': 'amount_total', 'type': 'currency', 'header': 'Total Amount'},
                    {'name': 'state', 'type': 'text', 'header': 'Status', 'transform': 'title'}
                ],
                'sheet_name': 'Sales Orders',
                'filter_domain': "[('state', 'in', ['sale', 'done'])]"
            },
            'products': {
                'model': 'product.product',
                'fields': [
                    {'name': 'name', 'type': 'text', 'header': 'Product Name'},
                    {'name': 'default_code', 'type': 'text', 'header': 'SKU'},
                    {'name': 'list_price', 'type': 'currency', 'header': 'Sale Price'},
                    {'name': 'qty_available', 'type': 'number', 'header': 'Available Qty'},
                    {'name': 'categ_id', 'type': 'text', 'header': 'Category'}
                ],
                'sheet_name': 'Products',
                'filter_domain': "[('sale_ok', '=', True)]"
            }
        }
        
        if template_key not in templates:
            raise ValidationError(_('Template not found'))
        
        template = templates[template_key]
        
        # Set model
        model = self.env['ir.model'].search([('model', '=', template['model'])], limit=1)
        if not model:
            raise ValidationError(_('Model {} not found').format(template['model']))
        
        # Update mapping settings
        self.model_id = model.id
        self.sheet_name = template['sheet_name']
        self.filter_domain = template.get('filter_domain', '')
        self.include_headers = True
        self.custom_headers = True
        
        # Clear existing field mappings
        self.field_mapping_ids.unlink()
        
        # Create new field mappings
        sequence = 10
        for field_config in template['fields']:
            field_obj = self.env['ir.model.fields'].search([
                ('model_id', '=', model.id),
                ('name', '=', field_config['name'])
            ], limit=1)
            
            if field_obj:
                mapping_vals = {
                    'mapping_id': self.id,
                    'sequence': sequence,
                    'mapping_type': 'field',
                    'odoo_field': field_obj.id,
                    'gsheets_column': chr(65 + (sequence // 10) - 1),  # A, B, C, etc.
                    'field_type': field_config.get('type', 'text'),
                    'custom_header': field_config.get('header', field_obj.field_description),
                }
                
                # Add specific formatting options
                if field_config.get('transform'):
                    mapping_vals['text_transform'] = field_config['transform']
                if field_config.get('type') == 'currency':
                    mapping_vals['number_format'] = 'currency'
                    mapping_vals['decimal_places'] = 2
                
                self.env['gsheets.field.mapping'].create(mapping_vals)
                sequence += 10
        
        return True


class GSheetsFieldMapping(models.Model):
    _name = 'gsheets.field.mapping'
    _description = 'Google Sheets Field Mapping Detail'
    _order = 'sequence, id'

    mapping_id = fields.Many2one('gsheets.mapping', string='Mapping', required=True, ondelete='cascade')
    sequence = fields.Integer('Sequence', default=10)
    
    # Odoo Field or Custom Expression
    mapping_type = fields.Selection([
        ('field', 'Odoo Field'),
        ('expression', 'Custom Expression'),
        ('computed', 'Computed Field')
    ], string='Mapping Type', default='field', required=True)
    
    odoo_field = fields.Many2one('ir.model.fields', string='Odoo Field', 
                                domain="[('model_id', '=', parent.model_id)]", ondelete='cascade')
    custom_expression = fields.Text('Custom Expression', 
                                   help='Python expression using "record" variable. E.g.: record.partner_id.country_id.name')
    
    # Google Sheets Column
    gsheets_column = fields.Char('Google Sheets Column', required=True, 
                                help='Column letter (A, B, C, etc.) or column name')
    custom_header = fields.Char('Custom Header Name', help='Custom name for this column header')
    
    # Field Configuration and Formatting
    field_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('currency', 'Currency'),
        ('date', 'Date'),
        ('datetime', 'Date & Time'),
        ('boolean', 'Boolean'),
        ('percentage', 'Percentage')
    ], string='Field Type', default='text')
    
    # Text Formatting
    text_transform = fields.Selection([
        ('none', 'No Transform'),
        ('upper', 'UPPERCASE'),
        ('lower', 'lowercase'),
        ('title', 'Title Case'),
        ('capitalize', 'Capitalize First')
    ], string='Text Transform', default='none')
    
    # Number Formatting
    decimal_places = fields.Integer('Decimal Places', default=2)
    number_format = fields.Selection([
        ('default', 'Default'),
        ('thousand_sep', 'Thousand Separator'),
        ('currency', 'Currency Format'),
        ('percentage', 'Percentage'),
        ('scientific', 'Scientific Notation')
    ], string='Number Format', default='default')
    currency_symbol = fields.Char('Currency Symbol', default='$')
    
    # Date Formatting
    date_format = fields.Selection([
        ('iso', 'YYYY-MM-DD'),
        ('us', 'MM/DD/YYYY'),
        ('eu', 'DD/MM/YYYY'),
        ('long', 'Month DD, YYYY'),
        ('custom', 'Custom Format')
    ], string='Date Format', default='iso')
    custom_date_format = fields.Char('Custom Date Format', default='%Y-%m-%d',
                                    help='Python strftime format. E.g.: %Y-%m-%d %H:%M:%S')
    
    # Boolean Formatting
    true_value = fields.Char('True Value', default='Yes')
    false_value = fields.Char('False Value', default='No')
    
    # Relationship Field Handling
    relation_display = fields.Selection([
        ('name', 'Display Name'),
        ('id', 'ID'),
        ('custom', 'Custom Field'),
        ('count', 'Count (for x2many)')
    ], string='Relation Display', default='name')
    relation_field = fields.Char('Relation Field', help='Field to display from related record')
    relation_separator = fields.Char('Many2many Separator', default=', ')
    
    # Default and Conditional Values
    default_value = fields.Char('Default Value')
    use_condition = fields.Boolean('Use Condition', default=False)
    condition_expression = fields.Text('Condition Expression', 
                                      help='Python expression returning True/False. E.g.: record.state == "done"')
    condition_true_value = fields.Char('Value if True')
    condition_false_value = fields.Char('Value if False')
    
    # Validation
    is_required = fields.Boolean('Required')
    validate_expression = fields.Text('Validation Expression',
                                     help='Python expression for validation. Return True if valid.')
    
    # Advanced Options
    skip_empty = fields.Boolean('Skip if Empty', default=False, help='Skip this field if value is empty')
    apply_function = fields.Selection([
        ('none', 'None'),
        ('sum', 'Sum (for numbers)'),
        ('count', 'Count'),
        ('avg', 'Average'),
        ('max', 'Maximum'),
        ('min', 'Minimum')
    ], string='Apply Function', default='none', help='Apply function to the field value')
    
    @api.constrains('odoo_field', 'gsheets_column', 'mapping_type')
    def _check_unique_mapping(self):
        """Ensure unique field mappings"""
        for record in self:
            # Only check for duplicate odoo_field when mapping_type is 'field'
            if record.mapping_type == 'field' and record.odoo_field:
                duplicate = self.search([
                    ('mapping_id', '=', record.mapping_id.id),
                    ('odoo_field', '=', record.odoo_field.id),
                    ('mapping_type', '=', 'field'),
                    ('id', '!=', record.id)
                ])
                if duplicate:
                    raise ValidationError(_('Field %s is already mapped.') % record.odoo_field.name)
            
            # Always check for duplicate column names
            duplicate_col = self.search([
                ('mapping_id', '=', record.mapping_id.id),
                ('gsheets_column', '=', record.gsheets_column),
                ('id', '!=', record.id)
            ])
            if duplicate_col:
                raise ValidationError(_('Column %s is already mapped.') % record.gsheets_column)
    
    @api.constrains('mapping_type', 'odoo_field', 'custom_expression')
    def _check_mapping_configuration(self):
        """Validate mapping configuration based on type"""
        for record in self:
            if record.mapping_type == 'field' and not record.odoo_field:
                raise ValidationError(_('Odoo Field is required when Mapping Type is "Odoo Field".'))
            elif record.mapping_type in ['expression', 'computed'] and not record.custom_expression:
                raise ValidationError(_('Custom Expression is required when Mapping Type is "Custom Expression" or "Computed Field".'))

    @api.onchange('mapping_type')
    def _onchange_mapping_type(self):
        """Clear fields based on mapping type"""
        if self.mapping_type == 'field':
            self.custom_expression = False
        else:
            self.odoo_field = False
    
    def get_formatted_value(self, record):
        """Get the formatted value for this field mapping"""
        try:
            # Get raw value based on mapping type
            if self.mapping_type == 'field' and self.odoo_field:
                raw_value = self._get_field_value(record, self.odoo_field.name)
            elif self.mapping_type in ['expression', 'computed'] and self.custom_expression:
                raw_value = self._evaluate_expression(record, self.custom_expression)
            else:
                raw_value = self.default_value or ''
            
            # Apply condition if configured
            if self.use_condition and self.condition_expression:
                condition_result = self._evaluate_expression(record, self.condition_expression)
                if condition_result:
                    raw_value = self.condition_true_value or raw_value
                else:
                    raw_value = self.condition_false_value or raw_value
            
            # Skip if empty and configured to do so
            if self.skip_empty and not raw_value:
                return ''
            
            # Apply formatting based on field type
            return self._format_value(raw_value)
            
        except Exception as e:
            if self.mapping_id.error_action == 'raise_error':
                raise
            elif self.mapping_id.error_action == 'use_default':
                return self.default_value or ''
            else:  # skip
                return f'Error: {str(e)}'
    
    def _get_field_value(self, record, field_path):
        """Get field value supporting nested field access"""
        try:
            # Support nested field access like partner_id.country_id.name
            value = record
            for field_part in field_path.split('.'):
                value = value[field_part]
                if not value:
                    break
            return value
        except Exception:
            return None
    
    def _evaluate_expression(self, record, expression):
        """Safely evaluate Python expressions"""
        try:
            # Create safe evaluation context
            safe_dict = {
                'record': record,
                'env': record.env,
                'time': __import__('time'),
                'datetime': __import__('datetime'),
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'sum': sum,
                'max': max,
                'min': min,
            }
            return eval(expression, {"__builtins__": {}}, safe_dict)
        except Exception as e:
            _logger.warning(f'Expression evaluation failed: {expression}, Error: {str(e)}')
            return None
    
    def _format_value(self, value):
        """Format value based on field type and formatting options"""
        if not value and value != 0 and value is not False:
            return self.default_value or ''
        
        try:
            # Boolean formatting
            if self.field_type == 'boolean' or isinstance(value, bool):
                return self.true_value if value else self.false_value
            
            # Date/DateTime formatting
            elif self.field_type in ['date', 'datetime'] and hasattr(value, 'strftime'):
                return self._format_date(value)
            
            # Number formatting
            elif self.field_type in ['number', 'currency', 'percentage'] and isinstance(value, (int, float)):
                return self._format_number(value)
            
            # Text formatting
            elif self.field_type == 'text' or isinstance(value, str):
                return self._format_text(str(value))
            
            # Relationship formatting
            elif hasattr(value, '_name'):  # Odoo recordset
                return self._format_relation(value)
            
            else:
                return str(value)
                
        except Exception as e:
            _logger.warning(f'Value formatting failed: {value}, Error: {str(e)}')
            return str(value) if value else ''
    
    def _format_date(self, date_value):
        """Format date values"""
        if not date_value:
            return ''
        
        format_map = {
            'iso': '%Y-%m-%d',
            'us': '%m/%d/%Y',
            'eu': '%d/%m/%Y',
            'long': '%B %d, %Y',
        }
        
        if self.date_format == 'custom' and self.custom_date_format:
            date_format = self.custom_date_format
        else:
            date_format = format_map.get(self.date_format, '%Y-%m-%d')
        
        if self.field_type == 'datetime':
            date_format += ' %H:%M:%S'
        
        return date_value.strftime(date_format)
    
    def _format_number(self, number_value):
        """Format number values"""
        if self.field_type == 'percentage':
            return f"{number_value * 100:.{self.decimal_places}f}%"
        elif self.field_type == 'currency':
            return f"{self.currency_symbol}{number_value:,.{self.decimal_places}f}"
        elif self.number_format == 'thousand_sep':
            return f"{number_value:,.{self.decimal_places}f}"
        elif self.number_format == 'scientific':
            return f"{number_value:.{self.decimal_places}e}"
        else:
            return f"{number_value:.{self.decimal_places}f}"
    
    def _format_text(self, text_value):
        """Format text values"""
        if self.text_transform == 'upper':
            return text_value.upper()
        elif self.text_transform == 'lower':
            return text_value.lower()
        elif self.text_transform == 'title':
            return text_value.title()
        elif self.text_transform == 'capitalize':
            return text_value.capitalize()
        else:
            return text_value
    
    def _format_relation(self, relation_value):
        """Format relationship field values"""
        if not relation_value:
            return ''
        
        if self.relation_display == 'count':
            return str(len(relation_value))
        elif self.relation_display == 'id':
            return ', '.join(str(r.id) for r in relation_value) if len(relation_value) > 1 else str(relation_value.id)
        elif self.relation_display == 'custom' and self.relation_field:
            values = []
            for record in relation_value:
                try:
                    val = self._get_field_value(record, self.relation_field)
                    values.append(str(val) if val else '')
                except:
                    values.append('')
            return self.relation_separator.join(values)
        else:  # 'name' or default
            return self.relation_separator.join(relation_value.mapped('display_name')) 