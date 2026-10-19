from odoo import models ,fields

class SparePart(models.Model):
    _name = 'spare.part'
    name = fields.Char(string="Spare Part")
    repair_id = fields.Many2one('repair.order', string="طلب الصيانة")
    spare_part_ids = fields.Many2many(
        'spare.part',
        'spare_part_self_rel',
        'spare_part_id_src',
        'spare_part_id_dest',
        string="Related Spare Parts"
    )
