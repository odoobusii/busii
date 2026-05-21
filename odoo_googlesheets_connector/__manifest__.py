{
    'name': 'Odoo Google Sheets Connector',
    'version': '18.0.2.3.3',
    'category': 'Tools',
    'summary': 'Advanced Google Sheets integration with enhanced field mapping, formatting, and automation',
    'description': """
        Advanced Google Sheets Sync for Odoo v17
        
        A comprehensive module for synchronizing Odoo data to Google Sheets with enterprise-level features.
        
        🔧 CORE FEATURES:
        • Multiple authentication methods (Service Account, OAuth2)
        • Flexible field mapping with custom expressions
        • Multiple sync modes (Append, Replace, Update)
        • Automated scheduling with cron jobs
        • Real-time error handling and logging
        
        📊 ADVANCED FIELD MAPPING:
        • Standard Odoo fields mapping
        • Custom Python expressions (e.g., record.partner_id.country_id.name)
        • Computed fields with safe evaluation
        • Nested field access support
        • Conditional mapping with dynamic values
        
        🎨 COMPREHENSIVE DATA FORMATTING:
        • Text: UPPERCASE, lowercase, Title Case, Capitalize
        • Numbers: Currency, percentages, thousand separators, scientific notation
        • Dates: Multiple formats (ISO, US, EU, Long) + custom formats
        • Booleans: Custom True/False values (Yes/No, Active/Inactive, ✓/✗)
        • Relationships: Display name, ID, custom fields, or record count
        
        ⚡ ENHANCED SYNC CAPABILITIES:
        • Smart header management with custom positioning
        • Date range filtering for large datasets
        • Record validation before sync
        • Data preview functionality
        • Error handling: Skip, Use Default, or Raise Error
        • Enhanced update mode with intelligent key matching
        
        🎯 QUICK SETUP TEMPLATES:
        • Sales Orders Export (Order #, Customer, Date, Amount, Status)
        • Product Catalog (Name, SKU, Price, Quantity, Category)
        • Customer List (Name, Email, Phone, City, Country)
        • Invoice Report (Invoice #, Customer, Date, Amount, Status)
        
        📈 ADVANCED FILTERING & MONITORING:
        • Domain-based record filtering
        • Date range filters
        • Record limits for performance
        • Detailed sync logs with metrics
        • Configuration validation
        • Performance tracking
        
        🛠️ EXPRESSION SYSTEM:
        • Safe Python expression evaluation
        • Access to common functions (len, sum, max, min)
        • Date/time calculations
        • Mathematical operations
        • Complex conditional logic
        
        💼 USE CASES:
        • Financial reporting with formatted numbers
        • Customer analysis with relationship data
        • Inventory reports with status indicators
        • Sales dashboards with calculated metrics
        • Automated data exports for external teams
        
        🔒 SECURITY & RELIABILITY:
        • Secure expression evaluation
        • Comprehensive error handling
        • User permission management
        • Data validation before sync
        • Audit trail with detailed logs
        
        ✨ NEW IN v2.0.0:
        • Enhanced field mapping with expressions
        • Advanced formatting options
        • Template system for quick setup
        • Header management
        • Date range filtering
        • Error handling improvements
        • Data preview functionality
        • Nested field access
        • Conditional value mapping
        
        📱 UPDATED IN v2.1.0:
        • Complete UI redesign with tabbed interface
        • All enhanced features now visible in forms
        • Advanced formatting controls in dedicated tabs
        • Relationship and condition configuration UI
        • Improved field mapping with inline editing
        • Enhanced search and filtering options
        
        📚 ENHANCED IN v2.2.0:
        • Comprehensive help system with examples
        • Step-by-step guidance for all features
        • Real-world expression examples library
        • Interactive tooltips and placeholders
        • Complete examples and help documentation tab
        • User-friendly error messages and validation
        • Professional formatting examples showcase
        
        🎨 LAYOUT FIX IN v2.2.1:
        • Removed bulky alert boxes for cleaner interface
        • Replaced with subtle guidance text
        • Improved spacing and visual hierarchy
        • Maintained comprehensive help tooltips
        • Streamlined form layouts for better usability
        
        🐛 TEMPLATE BUG FIX IN v2.2.2-3:
        • Fixed "Apply Template" button KeyError crash
        • Removed dependency on non-existent wizard model
        • Template now applies Sales Orders template directly
        • Clear success notification with applied field details
        • Robust error handling for template application
        • Ready-to-use functionality without additional setup
        
        🔧 FIELD MAPPING FIX IN v2.2.4:
        • Fixed "Field False is already mapped" error for custom expressions
        • Improved validation logic to handle custom expressions properly
        • Multiple custom expressions can now be used without conflicts
        • Enhanced constraint checking for better field mapping flexibility
        
        📚 GSPREAD API UPDATE IN v2.2.5:
        • Fixed gspread deprecation warning for worksheet.update() method
        • Updated all worksheet.update() calls to use named arguments
        • Compatible with latest gspread library versions
        • Eliminated deprecation warnings in logs
        
        🔄 RETRY & NOTIFICATION SYSTEM IN v2.2.6:
        • Added automatic retry mechanism for failed syncs
        • Configurable retry limits per mapping (default: 3 attempts)
        • Smart error handling: continue retrying until exhausted, then mark as error
        • Chatter integration for failure notifications
        • Notify specific partners on sync failures or when retries are exhausted
        • Enhanced sync logs with retry count information
        • Reset retry counter on successful syncs
        
        🐛 STABILITY IMPROVEMENTS IN v2.2.7:
        • Fixed view parsing errors for field mapping forms
        • Added proper chatter integration for mail.thread inheritance
        • Improved error handling with graceful fallbacks for field validation
        • Enhanced UI with dedicated retry and notification configuration tab
        
        🔧 RETRY SYSTEM REFACTOR IN v2.2.8:
        • Moved retry and notification settings from mapping level to configuration level
        • Centralized retry policy: all mappings under a config share the same retry settings
        • Chatter notifications now posted to configuration record instead of mappings
        • Simplified UI: retry settings now in Google Sheets Configuration form
        • Better organization: retry count tracked per configuration, not per mapping
        
        📊 ERROR STATUS VISIBILITY IN v2.2.9:
        • Enhanced error status display in configuration list view
        • Color-coded configurations: red for errors, orange for retry attempts
        • Prominent error alerts at top of configuration form
        • Retry status alerts showing current attempt progress
        • New search filters: "Has Retries", "Retry Exhausted", "Configured"
        • Error message searchable and optionally visible in tree view
        • State field displayed as colored badge in form view
        • Conditional error section only shows when there are actual errors
        
        🎯 GRANULAR RETRY & NOTIFICATION CONTROL IN v2.3.0:
        • Added mapping-level retry and notification settings (optional overrides)
        • Configuration-level settings act as defaults for all mappings
        • Mapping-level custom settings override configuration defaults
        • Independent retry counters: per-mapping or per-configuration
        • Flexible notification targets: mapping-specific or configuration-wide
        • Chatter integration: messages posted to mapping or configuration based on settings
        • Visual indicators in tree view for mappings with custom settings (blue highlight)
        • Enhanced search filters: "Custom Retry Settings", "Custom Notifications"
        • Smart fallback logic: always uses most specific settings available
        • Granular control: critical mappings can have higher retry limits and specific contacts
    """,
    'author': 'HSxTech',
    'website': 'https://www.hsxtech.net',
    'icon': '/odoo_googlesheets_connector/static/description/icon.png',
    'depends': [
        'base',
        'base_setup',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/gsheets_sync_security.xml',
        'data/ir_cron_data.xml',
        'views/gsheets_config_views.xml',
        'views/gsheets_sync_views.xml',
        'views/gsheets_mapping_views.xml',
        'views/menu_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'external_dependencies': {
        'python': [
            'google-auth',
            'google-auth-oauthlib',
            'google-auth-httplib2',
            'google-api-python-client',
            'gspread',
        ],
    },
    "images": [
        "static/description/banner.gif",
    ],
    'installable': True,
    'application': True,
    'price': 0.00,
    'currency': 'USD',
    'auto_install': False,
    'license': 'LGPL-3',
} 
