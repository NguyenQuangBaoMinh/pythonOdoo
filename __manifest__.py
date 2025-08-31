{
    'name': 'User Export for YODY',
    'version': '16.0.1.0.0',
    'category': 'Administration',
    'summary': 'Export user data to CSV/Excel',
    'description': """
        Export user data with filtering options
        - Export all or active users only
        - Filter by groups or sales teams  
        - Export to CSV or Excel format
    """,
    'author': 'YODY IT Team',
    'website': 'https://yody.vn',
    'depends': ['base', 'crm'],
    'data': [
        'security/user_export_security.xml',
        'security/ir.model.access.csv',
        'wizard/user_export_wizard_view.xml',  
        'views/user_export_views.xml',
        'views/menu_views.xml',                
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'LGPL-3',
}