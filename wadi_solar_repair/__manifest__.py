{
    'name': 'Wadi_solar_repair',
    'version': '1.0',
    'author': "Abdullah Riad Joher",
    'summary': 'Add some Featuer field to repair orders',
    'depends': ['base','stock', 'repair'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_view.xml',
        'views/spare_part_views.xml',
    ],
    'installable': True,
    'application': False,
}
