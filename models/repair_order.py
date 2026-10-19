from datetime import datetime, timedelta
import logging

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError

_logger = logging.getLogger(__name__)

class RepairOrder(models.Model):
    _inherit = 'repair.order'


    phone = fields.Char(
        string="Customer Phone",
        related="partner_id.phone",
        store=True,
        readonly=False
    )
    x_done_date = fields.Date(string="تاريخ تم الاصلاح", readonly=True)
    x_in_repair_date = fields.Date(string="تاريخ قيد الاصلاح", readonly=True)
    complaint_recipient = fields.Char(string="متلقي الشكوى")
    serial_number = fields.Char(string='الرقم التسلسلي')
    type_of_problem = fields.Char(string='نوع المشكله')
    date_reported = fields.Datetime(string="تاريخ الشراء", default=fields.Datetime.now)
    receiving = fields.Boolean(tracking=1)
    giving_spare = fields.Boolean(tracking=1)
    date_repair = fields.Datetime(string="تاريخ الدخول للصيانة", default=fields.Datetime.now)
    date_replacing = fields.Datetime(string="تاريخ الاستبدال", default=fields.Datetime.now)
    reason_of_replacing = fields.Char(string="سبب الاستبدال")
    replacement_notes = fields.Text(string="ملاحظات الاستبدال")
    sirial_number_of_replaced_battary = fields.Char(string="الرقم التسلسلي للبطارية المستبدلة")
    pdf_file_for_recharge = fields.Binary(string="Upload PDF", attachment=True)
    pdf_file_for_replacing = fields.Binary(string="Upload PDF", attachment=True)
    image_file = fields.Image(max_width=1028, max_height=1028)
    card_replacement_notes = fields.Text(string="ملاحظات الكرت المستبدل")
    date_card_replacement = fields.Datetime(string="تاريخ استبدال الكرت", default=fields.Datetime.now)
    pdf_file_for_card_replacement = fields.Binary(string="Upload PDF", attachment=True)
    cost_of_external_repair = fields.Float(string = "تكلفه الإصلاح الخارجي")
    cost_of_replacement = fields.Float(string = "تكلفه الإستبدال")

    # =========================
    # Repair Hold / تعليق الإصلاح
    # =========================

    is_on_hold = fields.Boolean(
        string="معلق",
        default=False,
        copy=False,
        tracking=True,
        readonly=True,
    )

    hold_reason = fields.Char(
        string="سبب التعليق",
        copy=False,
        tracking=True,
    )

    hold_date = fields.Datetime(
        string="تاريخ التعليق",
        copy=False,
        readonly=True,
        tracking=True,
    )

    hold_user_id = fields.Many2one(
        'res.users',
        string="تم التعليق بواسطة",
        copy=False,
        readonly=True,
        tracking=True,
    )

    total_hold_hours = fields.Float(
        string="إجمالي ساعات التعليق",
        default=0.0,
        copy=False,
        readonly=True,
    )
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
        ('card_replacemenet','استبدال كرت'),
        ('external_repair', 'إصلاح خارجي'),
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
    
    def action_repair_done(self):

        if self.filtered('is_on_hold'):
            raise UserError(
                'لا يمكن إنهاء أمر الإصلاح وهو معلق. '
                'قم باستئناف الإصلاح أولاً.'
            )

        res = super(RepairOrder, self).action_repair_done()

        for rec in self:
            rec.x_done_date = fields.Date.today()

        return res
    
    def write(self, vals):
        res = super(RepairOrder, self).write(vals)
        for rec in self:
            if 'state' in vals and vals.get('state') == 'under_repair':
                rec.x_in_repair_date = fields.Date.today()
        return res

    # دالة تعليق الإصلاح 
    
    def action_put_on_hold(self):
        for rec in self:

            # التعليق مسموح فقط في تم التأكيد أو قيد الإصلاح
            if rec.state not in ('confirmed', 'under_repair'):
                raise UserError(
                    'يمكن تعليق أمر الإصلاح فقط عندما تكون حالته '
                    '"تم التأكيد" أو "قيد الإصلاح".'
                )

            if rec.is_on_hold:
                raise UserError('أمر الإصلاح معلق بالفعل.')

            if not rec.hold_reason:
                raise UserError('يجب إدخال سبب التعليق أولاً.')

            now = fields.Datetime.now()

            rec.write({
                'is_on_hold': True,
                'hold_date': now,
                'hold_user_id': self.env.user.id,
            })

            rec.message_post(
                body=(
                    '<b>تم تعليق أمر الإصلاح</b><br/>'
                    f'السبب: {rec.hold_reason}<br/>'
                    f'بواسطة: {self.env.user.name}'
                )
            )

        return True

    # دالة استئناف الإصلاح  
    def action_resume_repair(self):
        for rec in self:

            if not rec.is_on_hold:
                raise UserError('أمر الإصلاح غير معلق.')

            now = fields.Datetime.now()

            hold_hours = 0.0

            if rec.hold_date:
                hold_delta = now - rec.hold_date
                hold_hours = hold_delta.total_seconds() / 3600.0

            total_hours = rec.total_hold_hours + hold_hours

            previous_reason = rec.hold_reason or '-'
            previous_user = rec.hold_user_id.name or '-'

            rec.write({
                'is_on_hold': False,
                'total_hold_hours': total_hours,
                'hold_reason': False,
                'hold_date': False,
                'hold_user_id': False,
            })

            rec.message_post(
                body=(
                    '<b>تم استئناف أمر الإصلاح</b><br/>'
                    f'سبب التعليق السابق: {previous_reason}<br/>'
                    f'تم التعليق بواسطة: {previous_user}<br/>'
                    f'مدة التعليق: {hold_hours:.2f} ساعة'
                )
            )

        return True

    
    # حماية زر بدء الإصلاح
    def action_repair_start(self):
        if self.filtered('is_on_hold'):
            raise UserError(
                'لا يمكن بدء الإصلاح لأن أمر الإصلاح معلق. '
                'قم باستئناف الإصلاح أولاً.'
            )

        return super(RepairOrder, self).action_repair_start()


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
