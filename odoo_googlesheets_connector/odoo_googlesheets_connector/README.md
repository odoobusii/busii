# Odoo Google Sheets Sync

A comprehensive Odoo v17 module for synchronizing saved search results and Odoo data to Google Sheets.

## Features

- **Flexible Field Mapping**: Map any Odoo field to Google Sheets columns
- **Multiple Sync Modes**: Append, replace, or update existing data
- **Domain Filtering**: Use Odoo domains to filter data before syncing
- **Scheduled Syncs**: Automate synchronization with configurable intervals
- **Manual Sync**: Trigger syncs on-demand
- **Error Handling**: Comprehensive logging and error reporting
- **Security**: Support for both Service Account and OAuth2 authentication
- **Multi-Configuration**: Manage multiple Google Sheets configurations

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install the Module

1. Copy the `odoo_gsheets_sync` folder to your Odoo addons directory
2. Update the addons list in Odoo
3. Install the module from the Apps menu

### 3. Google Sheets API Setup

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API
4. Create credentials (Service Account recommended)
5. Download the JSON key file

## Configuration

### 1. Create Google Sheets Configuration

1. Go to **Google Sheets Sync > Configuration > Google Sheets Configurations**
2. Create a new configuration
3. Upload your service account JSON file
4. Enter your Google Sheets URL or ID
5. Test the connection

### 2. Create Field Mapping

1. Go to **Google Sheets Sync > Configuration > Field Mappings**
2. Create a new mapping
3. Select the Odoo model to sync
4. Define the Google Sheets worksheet name
5. Map Odoo fields to Google Sheets columns
6. Set sync mode and filters
7. Test the mapping

## Usage

### Manual Sync

- Use the "Test Mapping" button to manually sync data
- Monitor sync logs for results

### Scheduled Sync

- Configure sync intervals in the configuration
- The system will automatically sync based on the schedule
- Monitor logs for any errors

### Sync Modes

- **Append**: Add new data to existing sheets
- **Replace**: Clear existing data and write new data
- **Update**: Update existing records based on key field

## Supported Field Types

- Text fields (char, text)
- Numeric fields (integer, float)
- Date and datetime fields
- Boolean fields
- Many2one relationships (displays related record name)
- Many2many and One2many relationships (comma-separated values)

## Security

The module supports two authentication methods:

1. **Service Account** (Recommended): More secure for server-to-server communication
2. **OAuth2**: For user-specific access

## Monitoring

- View sync logs in **Google Sheets Sync > Monitoring > Sync Logs**
- Monitor configuration status and error messages
- Track sync performance and record counts

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Ensure your service account has proper permissions
2. **Permission Denied**: Check Google Sheets sharing settings
3. **Large Dataset Timeouts**: Use appropriate record limits
4. **Field Mapping Errors**: Verify field names and types

### Debug Mode

Enable debug logging in Odoo to see detailed sync information.

## Development

### Module Structure

```
odoo_gsheets_sync/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── gsheets_config.py
│   ├── gsheets_mapping.py
│   ├── gsheets_sync.py
│   └── res_config_settings.py
├── controllers/
│   ├── __init__.py
│   └── main.py
├── security/
│   ├── ir.model.access.csv
│   └── gsheets_sync_security.xml
├── views/
│   ├── gsheets_config_views.xml
│   ├── gsheets_mapping_views.xml
│   ├── gsheets_sync_views.xml
│   ├── menu_views.xml
│   └── res_config_settings_views.xml
├── data/
│   └── ir_cron_data.xml
├── static/
│   └── description/
│       ├── index.html
│       └── icon.png
├── requirements.txt
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This module is licensed under LGPL-3.

## Support

For support, questions, or feature requests, please contact the development team.

## Version History

- **17.0.1.0.0**: Initial release for Odoo v17 