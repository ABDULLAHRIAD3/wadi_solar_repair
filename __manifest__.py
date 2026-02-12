{
    'name': 'Wadi_solar_repair',
    'version': '1.1',
    'author': "Abdullah Riad Joher",
    'description': 'For add some Features in repair',
    "license": "LGPL-3",
    'summary': 'Add some Feature field to repair orders with KPI measurements',
    'depends': ['base', 'stock', 'repair', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_view.xml',
        'views/spare_part_views.xml',
        'views/repair_kpi_views.xml',
    ],
    'installable': True,
    'application': False,
}
