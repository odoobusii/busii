from odoo.models import api, Model
from odoo.tools.safe_eval import const_eval
from odoo.exceptions import ValidationError, UserError

class IrConfigParameter(Model):
    _inherit = "ir.config_parameter"

    @api.model
    def get_crm_facebook_config(self):
        get_param = self.sudo().get_param
        return {
            'crm_fb_app_id': const_eval(get_param("crm_facebook_leads.crm_fb_app_id", 'False')),
            'crm_fb_app_secret': get_param("crm_facebook_leads.crm_fb_app_secret", 'False'),
            'crm_fb_access_token': get_param("crm_facebook_leads.crm_fb_access_token", 'False'),
        }

    def action_fetch_facebook_leads(self):
        """
        Manually fetch Facebook leads from settings page
        """
        try:
            # CORRECTED: Use the model's method properly
            self.env['crm.lead'].get_facebook_leads()

            # Force reload of settings page to show updated state
            return {
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
        except Exception as e:
            _logger.error("Failed to fetch Facebook leads: %s", str(e))
            error_msg = f"Failed to fetch Facebook leads: {str(e)}"
            if "Error validating access token" in str(e):
                error_msg += "\n\nPlease check your Facebook access token in the settings above."
            raise UserError(error_msg)
