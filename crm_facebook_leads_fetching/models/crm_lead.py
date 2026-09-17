import re
import logging
import requests
from datetime import datetime, timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    facebook_lead_id = fields.Char(readonly=True)
    facebook_page_id = fields.Many2one(
        'crm.facebook.page', related='facebook_form_id.page_id',
        store=True, readonly=True)
    facebook_form_id = fields.Many2one('crm.facebook.form', readonly=True)
    facebook_adset_id = fields.Many2one('utm.adset', readonly=True)
    facebook_ad_id = fields.Many2one(
        'utm.medium', related='medium_id', store=True, readonly=True,
        string='Facebook Ad')
    facebook_campaign_id = fields.Many2one(
        'utm.campaign', related='campaign_id', store=True, readonly=True,
        string='Facebook Campaign')
    facebook_date_create = fields.Datetime(readonly=True)
    facebook_is_organic = fields.Boolean(readonly=True)

    # Custom fields for Facebook data
    flooring_area = fields.Char(string='Flooring Area', tracking=True)
    project_timeline = fields.Char(string='Project Timeline', tracking=True)
    callback_consent = fields.Boolean(string='Callback Consent', tracking=True)
    facebook_raw_data = fields.Text(string='Facebook Raw Data', help='Original Facebook lead data')
    facebook_address = fields.Char(string='Facebook Address', tracking=True, help='Address from Facebook lead')

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)',
         'This Facebook lead already exists!')
    ]

    def fetch_facebook_leads(self):
        """
        Manually fetch Facebook leads - called from button click
        """
        _logger.info("Manual Facebook leads fetch initiated by user %s", self.env.user.name)
        try:
            # CORRECTED: Call class method directly, not self.get_facebook_leads()
            self.env['crm.lead'].get_facebook_leads()

            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Success',
                    'message': 'Facebook leads fetched successfully! Check CRM for new leads.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error("Failed to fetch Facebook leads: %s", str(e))
            error_msg = f"Failed to fetch Facebook leads: {str(e)}"
            if "Error validating access token" in str(e):
                error_msg += "\n\nYour access token may have expired. Please go to Settings > Facebook Leads Configuration and get a new access token."
            raise UserError(error_msg)

    # Original method (unchanged)
    @api.model
    def get_facebook_leads(self):
        fb_api = "https://graph.facebook.com/v7.0/"
        for form in self.env['crm.facebook.form'].search([]):
            _logger.info('Starting to fetch leads from Form: %s' % form.name)
            params = {'access_token': form.access_token,
                      'fields': 'created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,is_organic'
                      }
            if form.date_retrieval:
                params.update({
                    'filtering': "[{'field': 'time_created', 'operator': 'GREATER_THAN', 'value': %s}]" % (
                        int(form.date_retrieval.timestamp())),
                })
            r = requests.get(fb_api + form.facebook_form_id + "/leads", params=params).json()
            if r.get('error'):
                # Don't raise error for all forms if one fails
                _logger.error("Error fetching leads for form %s: %s", form.name, r['error']['message'])
                continue
            self.lead_processing(r, form)
        _logger.info('Fetch of leads has ended')
        return True

    def get_ad(self, lead):
        ad_obj = self.env['utm.medium']
        if not lead.get('ad_id'):
            return ad_obj
        if not ad_obj.search(
                [('facebook_ad_id', '=', lead['ad_id'])]):
            return ad_obj.create({
                'facebook_ad_id': lead['ad_id'], 'name': lead['ad_name'], }).id

        return ad_obj.search(
            [('facebook_ad_id', '=', lead['ad_id'])], limit=1)[0].id

    def get_adset(self, lead):
        ad_obj = self.env['utm.adset']
        if not lead.get('adset_id'):
            return ad_obj

        # Use sudo() to bypass permission issues
        try:
            if not ad_obj.search([('facebook_adset_id', '=', lead['adset_id'])]):
                return ad_obj.sudo().create({
                    'facebook_adset_id': lead['adset_id'],
                    'name': lead.get('adset_name', 'Unknown AdSet'),
                }).id
            return ad_obj.search([('facebook_adset_id', '=', lead['adset_id'])], limit=1)[0].id
        except Exception as e:
            _logger.warning("Could not create AdSet: %s", str(e))
            return False

    def get_campaign(self, lead):
        campaign_obj = self.env['utm.campaign']
        if not lead.get('campaign_id'):
            return campaign_obj
        if not campaign_obj.search(
                [('facebook_campaign_id', '=', lead['campaign_id'])]):
            return campaign_obj.create({
                'facebook_campaign_id': lead['campaign_id'],
                'name': lead['campaign_name'], }).id

        return campaign_obj.search(
            [('facebook_campaign_id', '=', lead['campaign_id'])],
            limit=1)[0].id

    def prepare_lead_creation(self, lead, form):
        vals, notes = self.get_fields_from_data(lead, form)
        vals.update({
            'facebook_lead_id': lead['id'],
            'facebook_is_organic': lead['is_organic'],
            'name': self.get_opportunity_name(vals, lead, form),
            'description': "\n".join(notes),
            'team_id': form.team_id and form.team_id.id,
            'company_id': form.team_id and form.team_id.company_id and form.team_id.company_id.id or False,
            'campaign_id': form.campaign_id and form.campaign_id.id or self.get_campaign(lead),
            'source_id': form.source_id and form.source_id.id,
            'medium_id': form.medium_id and form.medium_id.id or self.get_ad(lead),
            'user_id': form.team_id and form.team_id.user_id and form.team_id.user_id.id or False,
            'facebook_adset_id': self.get_adset(lead),
            'facebook_form_id': form.id,
            'facebook_date_create': lead['created_time'].split('+')[0].replace('T', ' ')
        })
        return vals

    def lead_creation(self, lead, form):
        vals = self.prepare_lead_creation(lead, form)
        return self.create(vals)

    def get_opportunity_name(self, vals, lead, form):
        if not vals.get('name'):
            # Try to create a meaningful name
            name_parts = []
            if vals.get('contact_name'):
                name_parts.append(vals['contact_name'])
            if vals.get('partner_name'):
                name_parts.append(vals['partner_name'])
            if vals.get('email_from'):
                # Extract company from email
                email_parts = vals['email_from'].split('@')
                if len(email_parts) > 1:
                    domain = email_parts[1].split('.')[0]
                    name_parts.append(domain.title())

            if name_parts:
                vals['name'] = ' - '.join(name_parts)
            else:
                vals['name'] = '%s - %s' % (form.name, lead['id'])
        return vals['name']

    def get_fields_from_data(self, lead, form):
        """
        Main method to process Facebook lead data
        """
        # Store raw data
        raw_data = str(lead)

        # First process with smart mapping
        auto_vals = self._process_facebook_lead_data(lead)

        # Then apply form-specific mappings
        form_vals, notes = self._apply_form_mappings(lead, form)

        # Merge values (form mappings take priority)
        for key, value in form_vals.items():
            if value:
                auto_vals[key] = value

        # Add any unmapped fields to notes
        notes = self._add_unmapped_to_notes(lead, form, notes)

        # Add raw data to values
        auto_vals['facebook_raw_data'] = raw_data

        return auto_vals, notes

    def _process_facebook_lead_data(self, lead):
        """Smart processing of Facebook lead data"""
        vals = {}
        name_parts = {'first': '', 'last': ''}

        for field_name, field_value in lead.items():
            if not field_value:
                continue

            cleaned_value = self._clean_facebook_value(field_value)

            # Name fields - collect first and last names separately
            if self._is_name_field(field_name):
                name_type = self._get_name_type(field_name)
                if name_type == 'first':
                    name_parts['first'] = cleaned_value
                elif name_type == 'last':
                    name_parts['last'] = cleaned_value
                else:
                    # If it's full name, try to split
                    if ' ' in cleaned_value:
                        parts = cleaned_value.split(' ', 1)
                        name_parts['first'] = parts[0] if not name_parts['first'] else name_parts['first']
                        name_parts['last'] = parts[1] if not name_parts['last'] else name_parts['last']
                    else:
                        name_parts['first'] = cleaned_value

            # Email fields
            elif self._is_email_field(field_name):
                vals['email_from'] = cleaned_value

            # Phone/Mobile fields - ALL go to phone field
            elif self._is_phone_field(field_name):
                vals['phone'] = self._clean_phone_number(cleaned_value)

            # Address fields
            elif self._is_address_field(field_name):
                vals['facebook_address'] = cleaned_value
                # Also try to extract street from address
                if 'street' in field_name.lower():
                    vals['street'] = cleaned_value

            # Project timeline
            elif self._is_project_timeline_field(field_name):
                self._process_project_timeline_field(cleaned_value, vals)

            # Flooring area
            elif self._is_flooring_area_field(field_name):
                vals['flooring_area'] = cleaned_value

            # Callback consent
            elif self._is_callback_consent_field(field_name):
                vals['callback_consent'] = cleaned_value.lower() in ('yes', 'true', '1', 'y', 'yes_')

        # Combine first and last names
        if name_parts['first'] or name_parts['last']:
            contact_name = f"{name_parts['first']} {name_parts['last']}".strip()
            if contact_name:
                vals['contact_name'] = contact_name

        return vals

    def _get_name_type(self, field_name):
        """Determine if field is first name, last name, or full name"""
        field_lower = field_name.lower()

        if 'first' in field_lower or 'given' in field_lower:
            return 'first'
        elif 'last' in field_lower or 'surname' in field_lower or 'family' in field_lower:
            return 'last'
        else:
            return 'full'

    def _clean_facebook_value(self, value):
        """Clean Facebook form values"""
        if not value:
            return value

        # Remove underscores and extra spaces
        cleaned = str(value).replace('_', ' ').strip()
        cleaned = re.sub(r'\s+', ' ', cleaned)

        return cleaned

    def _is_name_field(self, field_name):
        """Check if field is a name field"""
        name_patterns = ['first name', 'last name', 'full name', 'name', 'contact name',
                         'first_name', 'last_name', 'full_name', 'contact_name',
                         'given name', 'surname', 'family name']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in name_patterns)

    def _is_email_field(self, field_name):
        """Check if field is an email field"""
        email_patterns = ['email', 'e-mail', 'mail', 'email_address', 'e_mail']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in email_patterns)

    def _is_phone_field(self, field_name):
        """Check if field is a phone field"""
        phone_patterns = ['phone', 'mobile', 'cell', 'telephone', 'contact_number',
                          'phone_number', 'mobile_number', 'phone number']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in phone_patterns)

    def _clean_phone_number(self, value):
        """Clean and format phone number"""
        if not value:
            return ''

        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', value)

        # Format Australian numbers
        if cleaned.startswith('61') and len(cleaned) > 10:
            cleaned = '+' + cleaned
        elif cleaned.startswith('04') and len(cleaned) == 10:
            cleaned = '+61' + cleaned[1:]
        elif len(cleaned) == 9 and cleaned.startswith('4'):
            cleaned = '+61' + cleaned

        return cleaned

    def _is_address_field(self, field_name):
        """Check if field is an address field"""
        address_patterns = ['address', 'street', 'city', 'suburb', 'postcode',
                            'zip code', 'state', 'country', 'location']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in address_patterns)

    def _is_project_timeline_field(self, field_name):
        """Check if field is project timeline field"""
        timeline_patterns = ['when_are_you_looking', 'timeline', 'timeframe',
                             'when do you need', 'completion', 'project timeline']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in timeline_patterns)

    def _process_project_timeline_field(self, value, vals):
        """Process project timeline and set expected closing date"""
        vals['project_timeline'] = value

        # Extract date from timeline
        expected_closing = self._extract_date_from_timeline(value)
        if expected_closing:
            vals['date_deadline'] = expected_closing

    def _extract_date_from_timeline(self, timeline_text):
        """Extract expected closing date from timeline text"""
        if not timeline_text:
            return None

        timeline_lower = timeline_text.lower()
        today = datetime.now()

        # Map timeline to days
        timeline_mapping = {
            'immediate': 7,
            'asap': 7,
            'urgent': 7,
            'within 1 week': 7,
            '1 week': 7,
            'within 2 weeks': 14,
            '2 weeks': 14,
            'within 1 month': 30,
            '1 month': 30,
            'within 2 months': 60,
            '2 months': 60,
            'within 3 months': 90,
            '3 months': 90,
            'within_the_next_3_months': 90,
            'within 6 months': 180,
            '6 months': 180,
            'within 1 year': 365,
            '1 year': 365,
        }

        # Check for matches
        for pattern, days in timeline_mapping.items():
            if pattern in timeline_lower:
                return (today + timedelta(days=days)).strftime('%Y-%m-%d')

        # Check for number patterns
        number_patterns = {
            r'(\d+)\s*day': 1,
            r'(\d+)\s*week': 7,
            r'(\d+)\s*month': 30,
            r'(\d+)\s*year': 365,
        }

        for pattern, multiplier in number_patterns.items():
            match = re.search(pattern, timeline_lower)
            if match:
                try:
                    num = int(match.group(1))
                    days = num * multiplier
                    return (today + timedelta(days=days)).strftime('%Y-%m-%d')
                except:
                    pass

        return None

    def _is_flooring_area_field(self, field_name):
        """Check if field is flooring area field"""
        area_patterns = ['square_meters', 'sqm', 'flooring_area',
                         'how_many_square', 'area', 'floor space']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in area_patterns)

    def _is_callback_consent_field(self, field_name):
        """Check if field is callback consent field"""
        consent_patterns = ['callback', 'call_back', 'contact_me',
                            'happy to call', 'permission to call', 'consent']
        field_lower = field_name.lower()
        return any(pattern in field_lower for pattern in consent_patterns)

    def _apply_form_mappings(self, lead, form):
        """Apply form-specific field mappings"""
        vals, notes = {}, []
        form_mapping = form.mappings.filtered(lambda m: m.odoo_field).mapped('facebook_field')

        for name, value in lead.items():
            if name not in form_mapping:
                continue

            odoo_field = form.mappings.filtered(lambda m: m.facebook_field == name).odoo_field
            if not odoo_field:
                continue

            # Convert value based on field type
            converted_value = self._convert_field_value(value, odoo_field.ttype)

            if converted_value is not None:
                # Special handling for phone fields - always map to 'phone' field
                if odoo_field.name == 'mobile' or 'phone' in odoo_field.name.lower():
                    vals['phone'] = self._clean_phone_number(value)
                else:
                    vals[odoo_field.name] = converted_value
                notes.append(f"{odoo_field.field_description}: {value}")

        return vals, notes

    def _convert_field_value(self, value, field_type):
        """Convert value to appropriate type for Odoo field"""
        if not value:
            return None

        try:
            if field_type in ('float', 'monetary'):
                numbers = re.findall(r'\d+\.?\d*', str(value))
                return float(numbers[0]) if numbers else 0.0

            elif field_type == 'integer':
                numbers = re.findall(r'\d+', str(value))
                return int(numbers[0]) if numbers else 0

            elif field_type in ('date', 'datetime'):
                if 'T' in value:
                    dt_str = value.split('+')[0].replace('T', ' ')
                    return dt_str
                return value

            elif field_type == 'boolean':
                return str(value).lower() in ('yes', 'true', '1', 'y', 'yes_')

            elif field_type == 'selection':
                return str(value)

            else:
                return str(value)

        except Exception as e:
            _logger.error(f"Error converting value {value} for type {field_type}: {e}")
            return str(value)

    def _add_unmapped_to_notes(self, lead, form, existing_notes):
        """Add unmapped fields to notes"""
        notes = existing_notes.copy() if existing_notes else []
        form_mapped_fields = form.mappings.filtered(lambda m: m.odoo_field).mapped('facebook_field')

        for name, value in lead.items():
            if name not in form_mapped_fields and name not in ['id', 'created_time', 'is_organic']:
                notes.append(f"{name}: {value}")

        return notes

    def process_lead_field_data(self, lead):
        field_data = lead.pop('field_data')
        lead_data = dict(lead)
        lead_data.update([(l['name'], l['values'][0])
                          for l in field_data
                          if l.get('name') and l.get('values')])
        return lead_data

    def lead_processing(self, r, form):
        if not r.get('data'):
            return
        for lead in r['data']:
            lead = self.process_lead_field_data(lead)
            if not self.search(
                    [('facebook_lead_id', '=', lead.get('id')), '|', ('active', '=', True), ('active', '=', False)]):
                self.lead_creation(lead, form)

        # /!\ NOTE: Once finished a page let us commit that
        try:
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()

        if r.get('paging') and r['paging'].get('next'):
            _logger.info('Fetching a new page in Form: %s' % form.name)
            self.lead_processing(requests.get(r['paging']['next']).json(), form)
        return

    @api.model
    def get_facebook_leads(self):
        fb_api = "https://graph.facebook.com/v7.0/"
        for form in self.env['crm.facebook.form'].search([]):
            # /!\ NOTE: We have to try lead creation if it fails we just log it into the Lead Form?
            _logger.info('Starting to fetch leads from Form: %s' % form.name)
            params = {'access_token': form.access_token,
                      'fields': 'created_time,field_data,ad_id,ad_name,adset_id,adset_name,campaign_id,campaign_name,is_organic'
                      }
            if form.date_retrieval:
                params.update({
                    'filtering': "[{'field': 'time_created', 'operator': 'GREATER_THAN', 'value': %s}]" % (
                        int(form.date_retrieval.timestamp())),
                })
            r = requests.get(fb_api + form.facebook_form_id + "/leads", params=params).json()
            if r.get('error'):
                raise UserError(r['error']['message'])
            self.lead_processing(r, form)
        _logger.info('Fetch of leads has ended')
