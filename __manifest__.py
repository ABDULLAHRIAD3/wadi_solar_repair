{
    'name': 'Wadi_solar_repair',
    'version': '1.0',
    'author': "Abdullah Riad Joher",
    'summary': 'Add some Featuer field to repair orders',
<<<<<<< HEAD
    'depends': ['repair'],
    'data': [
        'views/repair_order_view.xml',
=======
    'depends': ['base','stock', 'repair'],
    'data': [
        'security/ir.model.access.csv',
        'views/repair_order_view.xml',
        'views/spare_part_views.xml',
>>>>>>> 4ac5aff (تحديث الكود بعد نقل كل التعديلات من المديول الرسمي للاودو للتوريث)
    ],
    'installable': True,
    'application': False,
}
