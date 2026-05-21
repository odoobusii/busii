from odoo import http
from odoo.http import request
import json


class GSheetsSyncController(http.Controller):

    @http.route('/gsheets/sync/<int:mapping_id>', type='http', auth='user', methods=['POST'])
    def manual_sync(self, mapping_id, **kwargs):
        """Manual sync endpoint"""
        try:
            mapping = request.env['gsheets.mapping'].browse(mapping_id)
            if not mapping.exists():
                return json.dumps({'success': False, 'error': 'Mapping not found'})
            
            # Check access rights
            if not request.env.user.has_group('base.group_system'):
                return json.dumps({'success': False, 'error': 'Access denied'})
            
            # Perform sync
            sync_service = request.env['gsheets.sync']
            result = sync_service.sync_mapping(mapping, force=True)
            
            return json.dumps(result)
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})

    @http.route('/gsheets/test-connection/<int:config_id>', type='http', auth='user', methods=['POST'])
    def test_connection(self, config_id, **kwargs):
        """Test connection endpoint"""
        try:
            config = request.env['gsheets.config'].browse(config_id)
            if not config.exists():
                return json.dumps({'success': False, 'error': 'Configuration not found'})
            
            # Check access rights
            if not request.env.user.has_group('base.group_system'):
                return json.dumps({'success': False, 'error': 'Access denied'})
            
            # Test connection
            sync_service = request.env['gsheets.sync']
            result = sync_service.test_connection(config)
            
            return json.dumps(result)
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)})

    @http.route('/gsheets/test-mapping/<int:mapping_id>', type='http', auth='user', methods=['POST'])
    def test_mapping(self, mapping_id, **kwargs):
        """Test mapping endpoint"""
        try:
            mapping = request.env['gsheets.mapping'].browse(mapping_id)
            if not mapping.exists():
                return json.dumps({'success': False, 'error': 'Mapping not found'})
            
            # Check access rights
            if not request.env.user.has_group('base.group_system'):
                return json.dumps({'success': False, 'error': 'Access denied'})
            
            # Test mapping
            sync_service = request.env['gsheets.sync']
            result = sync_service.test_mapping(mapping)
            
            return json.dumps(result)
            
        except Exception as e:
            return json.dumps({'success': False, 'error': str(e)}) 