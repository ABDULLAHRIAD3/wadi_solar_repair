from importlib.metadata import requires

from odoo import models, fields ,api
from odoo.exceptions import ValidationError, UserError


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    serial_number = fields.Char(string='الرقم التسلسلي')
    type_of_problem = fields.Char(string='نوع المشكله')
    date_reported = fields.Datetime(string="تاريخ الشراء", default=fields.Datetime.now)
    receiving = fields.Boolean(tracking=1)
    giving_spare = fields.Boolean(tracking=1)
    
    
    repair_parts = fields.Many2one('product.product', string='أجزاء الإصلاح')
    repair_order_ids = fields.One2many('repair.order', 'repair_parts', string='أوامر الإصلاح')

     
    @api.constrains('type_of_problem')
    def _check_type_of_problem(self):
        for record in self:
            if not record.type_of_problem:
                raise UserError('ادخل نوع المشكلة')


