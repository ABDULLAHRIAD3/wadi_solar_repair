
from datetime import datetime, timedelta
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    serial_number = fields.Char(string='الرقم التسلسلي')
    type_of_problem = fields.Char(string='نوع المشكله')
    date_reported = fields.Datetime(string="تاريخ الشراء", default=fields.Datetime.now)
    receiving = fields.Boolean(tracking=1)
    giving_spare = fields.Boolean(tracking=1)

    pdf_file_for_recharge = fields.Binary(string="Upload PDF", attachment=True)
    pdf_file_for_replacing = fields.Binary(string="Upload PDF", attachment=True)
    image_file = fields.Image(max_width=1028, max_height=1028)
    #Spare Part 
    spare_part_ids = fields.Many2many(
        'spare.part',
        'repair_order_spare_part_rel',
        'repair_order_id',
        'spare_part_id',
        string="Used Parts",
        )

    actions_taken = fields.Selection([
        ('replacing','استبدال'),
        ('repair','صيانة'),
        ('re_charge','اعادة شحن'),
    ],
    string='الاجراءات المتخذة',
    default='repair',
    )

    repair_parts = fields.Many2one('product.product', string='أجزاء الإصلاح')
    repair_order_ids = fields.One2many('spare.part', 'repair_id', string='قطع الصيانة')



    @api.constrains('type_of_problem')
    def _check_type_of_problem(self):
        for record in self:
            if not record.type_of_problem:
                raise UserError('ادخل نوع المشكلة')
            
    def cron_notify_unfinished_repairs(self):
        _logger.info("بدأ تنفيذ cron_notify_unfinished_repairs")
        today = datetime.today().date()
    
        try:
            all_orders = self.search([
                ('state', '!=', 'done')
            ])
            _logger.info(f"تم العثور على {len(all_orders)} طلب إصلاح")
    
            for order in all_orders:
                if not order.create_date:
                    _logger.warning(f" الطلب {order.id} لا يحتوي create_date")
                    continue
                
                create_date = order.create_date.date()
                deadline = create_date + timedelta(days=3)  
    
                # نرسل التنبيه فقط إذا اليوم = deadline
                if today == deadline:
                    _logger.info(f" جدولة نشاط لطلب {order.name}، الموعد النهائي: {deadline}")
    
                    existing = self.env['mail.activity'].search([
                        ('res_model', '=', 'repair.order'),
                        ('res_id', '=', order.id),
                        ('activity_type_id', '=', self.env.ref('mail.mail_activity_data_todo').id),
                        ('summary', '=', 'تنبيه: لم يتم إكمال الصيانة في موعدها'),
                    ])
                    if existing:
                        continue
                    
                    order.activity_schedule(
                        activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                        user_id=order.user_id.id if order.user_id else self.env.user.id,
                        summary='تنبيه: لم يتم إكمال الصيانة في موعدها',
                        note=f' لقد وصلت المهلة النهائية لإكمال طلب الإصلاح {order.name}، الرجاء المتابعة فورًا.',
                        date_deadline=deadline
                    )
    
        except Exception as e:
            _logger.error(" خطأ أثناء تنفيذ cron_notify_unfinished_repairs: %s", e)
            raise
        

